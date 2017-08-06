# -*- coding: UTF-8 -*-
import codecs
import sys
import os
import langid
import argparse
import Queue
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)s: %(message)s')
LOG = logging.getLogger('Language ID')


def worker(mq):
    while True:
        payload = mq.get()
        if payload is None:
            break
        try:
            infile = payload
            LangFilter(infile)
        except:
            logging.error('Failed at file: {0}'.format(infile))
        mq.task_done()


def langFilter(num_workers, inputdir):
    mq = Queue.Queue()
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(mq,))
        t.start()
        threads.append(t)

    for roots, dirs, files in os.walk(inputdir):
        for sfile in files:
            if os.path.isdir(sfile) or sfile.endswith('langen') or sfile.startswith('.DS_Store'):
                continue
            infile = os.path.abspath(os.path.join(roots, sfile))
            mq.put(infile)

    for i in range(num_workers):
        mq.put(None)
    for t in threads:
        t.join()


def LangFilter(infile):
    with codecs.open(infile, 'r', 'utf-8') as f:
        with codecs.open(infile + '.langen', 'w', 'utf-8') as fout:
            print 'Processing {}'.format(infile)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if langid.classify(line)[0] != 'en':
                    continue
                fout.write(line + u'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Language Filter')
    parser.add_argument('--workers', '-w', default=3, type=int, help='Number of threads.')
    parser.add_argument('--inputdir', '-i', required = True, help='Input Dir')
    args = parser.parse_args()

    langFilter(args.workers, args.inputdir)
