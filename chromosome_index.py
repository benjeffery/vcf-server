import pysam
from itertools import islice, takewhile
from operator import ne
from functools import partial
import bsddb
from struct import pack
from werkzeug.exceptions import NotFound
import config
import StringIO
from gzip import GzipFile

#TODO cache doesn't have locking....
cache = bsddb.hashopen('cacheindex.db')
tabix = pysam.Tabixfile(config.vcf_file)

def positions(chrom):
    reader = tabix.fetch(chrom)
    len_chrom = len(chrom)+1
    not_tab = partial(ne, '\t')
    for line in reader:
        line = islice(line, len_chrom, 20)
        yield int(''.join(takewhile(not_tab, line)))

def pack_bytes(fmt, seq):
    for num in seq:
        for char in pack(fmt, num):
            yield char

def response(query_data):
    return query_data

def gzip(data):
    out = StringIO.StringIO()
    f = GzipFile(fileobj=out, mode='w')
    f.write(data)
    f.close()
    return out.getvalue()

def handler(start_response, query_data):
    chrom = query_data['chrom']
    if chrom not in tabix.contigs:
        raise NotFound(chrom+' Chromosome name not found')
    try:
        data = cache[config.vcf_file+chrom+'_pos']
    except KeyError:
        #As the response is not sample dependant we can zip it up in the cache.
        data = gzip(bytes(bytearray(pack_bytes('<I', positions(chrom)))))
        cache[config.vcf_file+chrom+'_pos'] = data

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(data))),
                        ('Content-Encoding', 'gzip')]
    start_response(status, response_headers)
    yield data

