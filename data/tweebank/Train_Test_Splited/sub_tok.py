#python3
import codecs
import sys

# arg[1]: goldpos
# arg[2]: autopos

for line, line1 in zip(codecs.open(sys.argv[1], 'r', 'utf-8'), codecs.open(sys.argv[2], 'r', 'utf-8')):
    line = line.strip()
    if not line:
        print()
        continue
    linevec = line.split(u'\t')
    linevec1 = line1.strip().split(u'\t')
    linevec[3] = linevec1[3]
    linevec[4] = linevec1[4]
    print(u'\t'.join(linevec))

