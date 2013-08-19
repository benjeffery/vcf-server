import vcf
import pysam
from shove import Shove
from struct import pack
from werkzeug.exceptions import NotFound
import config
from itertools import chain
import thread

#TODO cache doesn't have locking....
#cache = Shove('bsddb://cache.db', 'memcache://localhost', sync=10)
cache = Shove(cache='memcache://localhost')
tabix = pysam.Tabixfile(config.vcf_file)
vcf_reader = vcf.Reader(filename=config.vcf_file)

def pack_bytes(fmt, seq):
    for num in seq:
        for char in pack(fmt, num):
            yield char

def generate_and_store(chrom, start, end, samples):
    all_sample_data = {}
    custom_vcf_reader = vcf.Reader(filename=config.vcf_file, wanted_samples=samples)
    for sample in samples:
        all_sample_data[sample] = [bytearray(), bytearray(), bytearray()]

    for i, snp in enumerate(custom_vcf_reader.fetch(chrom, start, end)):
        if (i % 100) == 0:
            print 'custom',i
        for sample_name in samples:
            sample = snp.genotype(sample_name)
            sample_data = all_sample_data[sample_name]
            sample_call = sample.data
            sample_data[0].append(pack('<B', sample_call.GT if sample_call.GT is not None else 0))
            if type(sample_call.AD) == list:
                sample_data[1].append(pack('<B', min(sample_call.AD[0], 255)))
                sample_data[2].append(pack('<B', min(sample_call.AD[1], 255)))
            else:
                sample_data[1].append(pack('<B', min(sample_call.AD, 255)))
                sample_data[2].append(pack('<B', 0))

    for sample in all_sample_data:
        all_sample_data[sample] = bytes(sum(all_sample_data[sample], bytearray()))

    def cache_data():
        for sample in all_sample_data:
            cache[':'.join((config.vcf_file, chrom, sample, str(start), str(end), '_geno'))] = all_sample_data[sample]
    thread.start_new_thread(cache_data, ())

    return all_sample_data

def response(query_data):
    return query_data

def handler(start_response, query_data):
    chrom = query_data['chrom']
    start = int(query_data['start'])
    end = int(query_data['end'])
    samples = query_data['samples'].split('~')

    if chrom not in tabix.contigs:
        raise NotFound(chrom+' Chromosome name not found')
    for sample in samples:
        if sample not in vcf_reader.samples:
            raise NotFound(sample+' sample not found')

    sample_data = bytearray()
    try:
        for sample in samples:
            sample_data += cache[
                ':'.join((config.vcf_file, chrom, sample, str(start), str(end), '_geno'))
            ]
    except KeyError:
        all_sample_data = generate_and_store(chrom, start, end, samples)
        for sample in samples:
            sample_data += all_sample_data[sample]
    data = bytes(sample_data)

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(data)))]
    start_response(status, response_headers)
    yield data

