#/usr/local/bin/python3
import codecs
import sys
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)s: %(message)s')
LOG = logging.getLogger('Character Set')

utf8_set = {}

def charSet(inputdir):
    for root, dirs, files in os.walk(inputdir):
        for sfile in files:
            if os.path.isdir(sfile) or not sfile.endswith('.tok'):
                continue
            LOG.info('Processing {} ...'.format(os.path.join(root, sfile)))
            with codecs.open(os.path.join(root, sfile), 'r', 'utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    linevec = line.split()
                    for word in linevec:
                        for c in word:
                            if c in utf8_set:
                                continue
                            print(c)
                            utf8_set[c] = 1 


def charSetMerge(inputfiles):
    for sfile in inputfiles:
        if os.path.isdir(sfile):
            continue
        LOG.info('Processing {} ...'.format(sfile))
        with codecs.open(sfile, 'r', 'utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                for c in line:
                    if c in utf8_set:
                        continue
                    print(c)
                    utf8_set[c] = 1 


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Character Set')
    parser.add_argument('inputdir', help='Input Dir')
    parser.add_argument('--inputfiles', '-i', nargs='+', help='Input Files')
    args = parser.parse_args()
    
    charSet(args.inputdir)
    #charSetMerge(args.inputfiles)

