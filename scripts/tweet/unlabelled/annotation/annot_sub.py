# -*- coding: UTF-8 -*-
#!/usr/bin/python
"""
Substitute new annotations with old annotations
@Author Yi Zhu
Upated 03/10/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse
import codecs
import json

def annotSub(old_json):
    old_sents = {}
    with codecs.open(old_json, 'r', 'utf-8') as f:
        data = json.loads(f.readline())
        for b in data['tweets']:
            for n in data['tweets'][b]:
                if n == 'locked' or n == 'assignedTo':
                    continue
                num = data['tweets'][b][n]['number']
                anno = data['tweets'][b][n]['anno']
                if num not in old_sents:
                    old_sents[num] = set([anno])
                else:
                    old_sents[num].add(anno)

    ct = 0
    with codecs.open('yzhu.json', 'r', 'utf-8') as f:
        with codecs.open('yzhu.json.update', 'w', 'utf-8') as fout:
            data = json.loads(f.readline())
            for b in data['tweets']:
                for n in data['tweets'][b]:
                    if n == 'locked' or n == 'assignedTo':
                        continue
                    num = data['tweets'][b][n]['number']
                    anno_old = data['tweets'][b][n]['anno']
                    if num not in old_sents:
                        continue
                    else:
                        for anno in old_sents[num]:
                            if anno_old == anno:
                                continue
                            data['tweets'][b][n]['anno'] = anno
                            ct += 1
                            break
            fout.write(json.dumps(data))
    print(ct)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Annotation substitution')
    parser.add_argument('old_json', help='old_json')
    A = parser.parse_args()
    
    annotSub(A.old_json)
