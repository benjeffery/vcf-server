import gzip
import sys
import itertools
import struct

class stream:
    def __init__(self, it):
        self.it = it

    def take(self, n):
        return ''.join(itertools.islice(self.it, 0, n))

    def int(self, n=1):
        result = struct.unpack('<'+('i'*n), self.take(4*n))
        return result[0] if n == 1 else result

    def long(self, n=1):
        return struct.unpack('<'+('q'*n), self.take(8*n))


with gzip.open(sys.argv[1], 'r ') as f:
    f = iter(f.read())
    f = stream(f)
    assert(f.take(4) == 'TBI\x01')
    (num_seq, preset, sc, bc, ec, meta, skip) = f.int(7)
    sequences = f.take(f.int()).split(chr(0))[:-1]
    index = {}
    for sequence in sequences:
        index[sequence] = {'l': [], 'b': {}}
        num_bin = f.int()
        print 'num_bin', num_bin
        for j in range(num_bin):
            bin_num = f.int()
            print 'bin', bin_num,
            chunk_len = f.int()
            print ' chunks', chunk_len,
            chunks = []
            for k in range(chunk_len):
                a = map(hex, f.long(2))
                print a,
                chunks.append(a)
            index[sequence]['b'][bin_num] = chunks
        index[sequence]['l'] = map(hex, f.long(f.int()))
        print index[sequence]['l']


import pprint
pprint.pprint(index)


# 		// read the index
# 		mIndex = new TIndex[mSeq.length];
# 		for (i = 0; i < mSeq.length; ++i) {
# 			// the binning index
# 			int n_bin = readInt(is);
# 			mIndex[i] = new TIndex();

# 			mIndex[i].b = new HashMap<Integer, TPair64[]>();
# 			for (j = 0; j < n_bin; ++j) {
# 				int bin = readInt(is);
# 				TPair64[] chunks = new TPair64[readInt(is)];
# 				for (k = 0; k < chunks.length; ++k) {
# 					long u = readLong(is);
# 					long v = readLong(is);
# 					chunks[k] = new TPair64(u, v); // in C, this is inefficient
# 				}
# 				mIndex[i].b.put(bin, chunks);
# 			}
# 			// the linear index
# 			mIndex[i].l = new long[readInt(is)];
# 			for (k = 0; k < mIndex[i].l.length; ++k)
# 				mIndex[i].l[k] = readLong(is);
# 		}
# 		// close
# 		is.close();
# 	}