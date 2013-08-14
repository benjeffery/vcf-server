beg = 0
end = 100000
list = [0] * 37450
i = 0
k = 0
#if (beg >= end) return 0;
if end >= 1 << 29:
    end = 1 << 29
end -= 1
list[i] = 0;
i += 1
for k in xrange(1 + (beg>>26), 1 + (end>>26)):
    print 1,k
    list[i] = k
    i += 1
for k in xrange(9 + (beg>>23), 9 + (end>>23)):
    print 2,k
    list[i] = k
    i += 1
for k in xrange(73 + (beg>>20), 73 + (end>>20)):
    print 3,k
    list[i] = k
    i += 1
for k in xrange(585 + (beg>>17), 585 + (end>>17)):
    print 4,k
    list[i] = k
    i += 1
for k in xrange(4681 + (beg>>14), 4681 + (end>>14)):
    print 5,k
    list[i] = k
    i += 1
print i

print list