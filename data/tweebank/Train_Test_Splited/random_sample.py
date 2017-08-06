import codecs
import random

random.seed(100)

num = 70
sents = []
with codecs.open('full_train_subtoken', 'r', 'utf-8') as f:
    sent = []
    for line in f:
        line = line.strip()
        if not line:
            sents.append(sent)
            sent = []
            continue
        sent.append(line)

sent_len = len(sents)

dev_ind = random.sample(range(sent_len), 70)
with codecs.open('dev_subtoken_goldpos', 'w', 'utf-8') as f:
    with codecs.open('train_subtoken', 'w', 'utf-8') as fn:
        for i in xrange(sent_len):
            if i in dev_ind:
                f.write(u'\n'.join(sents[i]) + u'\n\n')
            else:
                fn.write(u'\n'.join(sents[i]) + u'\n\n')

