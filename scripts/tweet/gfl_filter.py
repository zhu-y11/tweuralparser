# -*- coding: UTF-8 -*-
#!/usr/bin/python
"""
GFL Original Filtering
@Author Yi Zhu
Upated 03/20/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse
import codecs
import os
import re
import sys
import json
import numpy as np
import editdistance


def read_corpus(filename):
    f = codecs.open(filename, "r", "utf-8")
    corpus = []
    sentence = []
    for line in f:
        if line.strip() == "":
            corpus.append(u' '.join(sentence))
            sentence = []
            continue
        else:
            line = line.strip()
            cline = line.split(u"\t")
            sentence.append(cline[1])
    f.close()
    return corpus


def GFLFilter(inputdir):
    data = []
    all_data = []
    with codecs.open(os.path.join(inputdir, 'all_remove_multiple_submission.json'), 'r', 'utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            all_data.append(json.loads(line, encoding = 'utf-8'))
    data = [d['pos'].split() for d in all_data]
    data = [u' '.join([w[:w.rfind('/')] for w in d]) for d in data]
    datas = zip(data, all_data)

    tweebank_data = read_corpus(os.path.join(inputdir, 'all_mwe_preprocessed.conll'))

    print len(datas), len(tweebank_data) 

    for d, dj in datas[:]:
        if d in tweebank_data[:]:
            datas.remove((d, dj))
            tweebank_data.remove(d)

    print len(datas), len(tweebank_data)  
    datas = [d[1] for d in datas]
    with codecs.open(os.path.join(inputdir, 'rest.json'), 'w', 'utf-8') as f:
        for d in datas:
            f.write(json.dumps(d) + u'\n')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'GFL Filtering')
    parser.add_argument('inputdir', help='GFL original file path')

    A = parser.parse_args()
    
    GFLFilter(A.inputdir)
