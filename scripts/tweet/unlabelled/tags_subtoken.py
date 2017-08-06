# -*- coding: UTF-8 -*-
#!/usr/bin/python3
"""
Add auto POS tags for tweets
@Author Yi Zhu
Upated 03/31/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse
import codecs
import os
from subprocess import call
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)s: %(message)s')
LOG = logging.getLogger('Add Automatic POS Tags')


def addPos(input_dir):
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if not f.endswith('.tok'):
                continue
            input_file = os.path.join(root, f)
            fout_tp = codecs.open('gold_pos', 'w', 'utf-8')
            LOG.info('Processing {} ... '.format(input_file))
            with codecs.open(input_file, 'r', 'utf-8') as fin:
                for line in fin:
                    line = line.strip()
                    if not line:
                        continue
                    linevec = line.split()
                    fout_tp.write(u'\n'.join([w + u'\t' + u'N' for w in linevec]) + u'\n\n')
            fout_tp.close()
            with codecs.open('pred_pos', 'w', 'utf-8') as f:
                call(['../runTagger.sh', '--input-format', 'conll', '--output-format', 'conll', 
                    '--model', '../pretrained_models/tagging_model', 'gold_pos'], stdout = f)
            fout = codecs.open(input_file + '.pos.subtok', 'w', 'utf-8')
            with codecs.open('pred_pos', 'r', 'utf-8') as fin:
                sent = []
                for line in fin:
                    line = line.strip()
                    if not line:
                        sent = [sent[i][0] + u'/' + sent[i][1] for i in range(len(sent))]
                        fout.write(u'<ROOT>/<ROOT> ' + u' '.join(sent) + u' ||| \n')
                        sent = []
                        continue
                    linevec = line.split(u'\t')[:2]
                    sent.append(linevec)
            fout.close()
    os.remove('pred_pos')
    os.remove('gold_pos')


def deSubtoken(input_dir):
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if not f.endswith('.tok'):
                continue
            tok_lines = []
            subtok_lines = []

            input_file = os.path.join(root, f)
            LOG.info('Processing {} ... '.format(input_file))
            with codecs.open(input_file, 'r', 'utf-8') as fin:
                for line in fin:
                    line = line.strip()
                    if not line:
                        continue
                    linevec = line.split()
                    tok_lines.append(linevec)

            input_file = os.path.join(root, f) + '.pos.subtok'
            with codecs.open(input_file, 'r', 'utf-8') as fin:
                for line in fin:
                    line = line.strip()
                    if not line:
                        continue
                    linevec = line.split()
                    for i in range(1, len(linevec) - 1):
                        idx = linevec[i].rfind(u'/')
                        wp = linevec[i]
                        linevec[i] = [wp[:idx], wp[idx + 1:]]
                    subtok_lines.append(linevec)
            
            assert(len(tok_lines) == len(subtok_lines))
            #print(len(tok_lines))
            #print(len(subtok_lines))
            input_file = os.path.join(root, f) + '.pos'
            with codecs.open(input_file, 'w', 'utf-8') as fout:
                for i, tok_linevec in enumerate(tok_lines):
                    for j, tok in enumerate(tok_linevec):
                        subtok_lines[i][j + 1] = tok + '/' + subtok_lines[i][j + 1][1]
                fout.write(u'\n'.join([u' '.join(subtok_line) for subtok_line in subtok_lines]) + u'\n')

            input_file = os.path.join(root, f) + '.pos.subtok'
            os.remove(input_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'add automatic POS tags for tweets')
    parser.add_argument('input_dir', help='Input Dir')
    A = parser.parse_args()
    
    #addPos(A.input_dir)
    deSubtoken(A.input_dir)

