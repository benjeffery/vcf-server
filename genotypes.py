import vcf
from shove import Shove
from struct import pack
from werkzeug.exceptions import NotFound
import config

#TODO cache doesn't have locking....
cache = Shove('bsddb://cache.db', 'memcache://localhost')
tabix = vcf.Reader(filename=config.vcf_file)

def pack_bytes(fmt, seq):
    for num in seq:
        for char in pack(fmt, num):
            yield char

def response(query_data):
    return query_data

def handler(start_response, query_data):
    chrom = query_data['chrom']
    start = query_data['start']
    end = query_data['end']
    if chrom not in tabix.contigs:
        raise NotFound('Chromosome name not found')
    try:
        data = cache[config.vcf_file+chrom+str(start)+':'+str(end)+'_pos']
    except KeyError:
    
        data = bytes(bytearray(pack_bytes('<I', positions(chrom))))
        cache[config.vcf_file+chrom+str(start)+':'+str(end)+'_pos'] = data
        cache.sync()
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(data)))]
    start_response(status, response_headers)
    yield data

