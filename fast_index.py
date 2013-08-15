import pysam
import sys
import vcf
from itertools import islice, takewhile
from operator import ne
from functools import partial


def positions(chrom):
    f = pysam.Tabixfile(sys.argv[1])
    reader = f.fetch(chrom)
    len_chrom = len(chrom)+1
    not_tab = partial(ne, '\t')
    for line in reader:
        line = islice(line, len_chrom, 20)
        yield int(''.join(takewhile(not_tab, line)))



pos = list(islice(positions('MAL1'), 2000))
print pos[0], pos[-1]

def snp_info_primitives(rec):
    return {
            #'chrom': rec.CHROM,
            'pos': rec.POS,
            'ref': rec.REF,
            'alt': str(rec.ALT[0] if len(rec.ALT) == 1 else rec.ALT),
            'filter': rec.FILTER if type(rec.FILTER)==list else [rec.FILTER],
            'info': rec.INFO,
            'qual': rec.QUAL,
            'counts': map(get_sample_call_primitives(rec), SAMPLES),
            }

def good_snp(snp):
    if snp.FILTER:
        if 'Heterozygous' in snp.FILTER:
            return True
        if 'MendelianErrors' in snp.FILTER:
            return True
    return False

def snps_json():
    VCF_READER = vcf.Reader(filename=sys.argv[1])#, wanted_samples=SAMPLES)
    for snp in VCF_READER.fetch('MAL1', pos[0], pos[-1]):#pos[-1]) ]#if snp.INFO.get("HQS", False)]
        for sample in snp.samples:
             a = sample.data.AD
    #snps = filter(good_snp, snps)
    #result = {
    #     'start':start,
    #     'end': end,
    #     'snps': map(snp_info_primitives, snps),
    #     'samples': [{
    #         'name': sample,
    #     } for sample in SAMPLES]
    # }
    #response = json.dumps(result)
    #return response

snps_json()