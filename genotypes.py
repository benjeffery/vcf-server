import vcf
import pysam
from struct import pack
from werkzeug.exceptions import NotFound
import config
from itertools import chain
import thread
from file_dict import FileDict

#TODO cache doesn't have locking....
cache = FileDict('cache')
tabix = pysam.Tabixfile(config.vcf_file)
vcf_reader = vcf.Reader(filename=config.vcf_file)

def pack_bytes(fmt, seq):
    for num in seq:
        for char in pack(fmt, num):
            yield char

def generate_and_store(chrom, start, end, sample_data):
    needed_samples = [sample for sample in sample_data if sample_data[sample] is None]
    custom_vcf_reader = vcf.Reader(filename=config.vcf_file, wanted_samples=needed_samples)
    snp_data = [bytearray(), bytearray()] #REF, ALT
    for sample in needed_samples:
        sample_data[sample] = [bytearray(), bytearray(), bytearray()]
    for i, snp in enumerate(custom_vcf_reader.fetch(chrom, start, end-1)):
        snp_data[0].append(snp.REF)
        snp_data[1].append(str(snp.ALT[0]))
        for sample_name in needed_samples:
            sample = snp.genotype(sample_name)
            data = sample_data[sample_name]
            sample_call = sample.data
            #OUR VCFS don't have genotypes! LOL!
            # sample_data[0].append(pack('<B', sample_call.GT if sample_call.GT is not None else 0))
            if type(sample_call.AD) == list:
                data[0] += pack('<H', min(sample_call.AD[0], 255*255))
                data[1] += pack('<H', min(sample_call.AD[1], 255*255))
            else:
                data[0] += pack('<H', min(sample_call.AD, 255*255))
                data[1] += pack('<H', 0)
    for sample in needed_samples:
        sample_data[sample] = bytes(sum(sample_data[sample], bytearray()))
    snp_data = bytes(sum(snp_data, bytearray()))

    #Cache on a seperate thread so we can return
    def cache_data():
        cache[':'.join((config.vcf_file, chrom, str(start), str(end), '_snp'))] = snp_data
        for sample in needed_samples:
            cache[':'.join((config.vcf_file, chrom, sample, str(start), str(end), '_geno'))] = sample_data[sample]
    thread.start_new_thread(cache_data, ())

    return snp_data, sample_data

def response(query_data):
    return query_data

def handler(start_response, query_data):
    chrom = query_data['chrom']
    start = int(query_data['start'])
    end = int(query_data['end'])
    try:
        samples = query_data['samples'].split('~')
    except KeyError:
        samples = []

    if chrom not in tabix.contigs:
        raise NotFound(chrom+' Chromosome name not found')

    sample_data = {}
    missing = False
    try:
        snp_data = cache[':'.join((config.vcf_file, chrom, str(start), str(end), '_snp'))]
    except KeyError:
        missing = True
    for sample in samples:
        try:
            sample_data[sample] = cache[':'.join((config.vcf_file, chrom, sample, str(start), str(end), '_geno'))]
        except KeyError:
            sample_data[sample] = None
            missing = True
    if missing:
        snp_data, sample_data = generate_and_store(chrom, start, end, sample_data)
    output = bytearray()
    output += snp_data
    for sample in samples:
        output += sample_data[sample]
    output = bytes(output)
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    yield output

