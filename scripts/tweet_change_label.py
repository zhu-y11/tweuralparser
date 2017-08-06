import argparse
import codecs

A = argparse.ArgumentParser()
A.add_argument("input_file")
args = A.parse_args()

sents = []
with codecs.open(args.input_file, 'r', 'utf-8') as f:
    sent = []
    for line in f:
        line = line.strip()
        if not line:
            sents.append(sent)
            sent = []
            continue
        linevec = line.split(u'\t')
        linevec[7] = u'_'
        sent.append(u'\t'.join(linevec))

with codecs.open(args.input_file, 'w', 'utf-8') as f:
    for sent in sents:
        f.write(u'\n'.join(sent) + u'\n\n')
