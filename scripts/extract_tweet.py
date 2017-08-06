# -*- coding: UTF-8 -*-
#!/usr/bin/python
"""
Extract Tweets
@Author Yi Zhu
Upated 02/17/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse
import codecs
import os
import bz2
import thread
import json

def extractTweets(inputdir):
    for roots, dirs, files in os.walk(inputdir):
        for f in files:
            if os.path.isdir(f):
                continue
            if not f.endswith('bz2'):
                continue
            #thread.start_new_thread(extractTweet, (os.path.abspath(os.path.join(roots, f)), ))
            extractTweet(os.path.abspath(os.path.join(roots, f)))


def extractTweet(infile):
    minute = os.path.basename(infile)
    minute = minute[:minute.find('.')]

    hour_dir = os.path.abspath(os.path.join(infile, os.path.pardir))
    hour = os.path.basename(hour_dir)

    day_dir = os.path.abspath(os.path.join(hour_dir, os.path.pardir))
    day = os.path.basename(day_dir)
    
    par_dir = os.path.abspath(os.path.join(day_dir, os.path.pardir))

    outfilename = '2016_07_{}_{}_{}'.format(day, hour, minute)
    fin = bz2.BZ2File(infile, 'r')
    fout = codecs.open(os.path.join(par_dir, outfilename), 'w', 'utf-8')
    print 'Processing {}'.format(outfilename)
    for line in fin:
        line = line.strip()
        if not line:
            continue
        line_json = json.loads(line)
        if u'text' not in line_json:
            continue
        if line_json[u'lang'] != u'en':
            continue
        text = line_json[u'text']
        text = u' '.join(text.split(u'\n')) + u'\n'
        fout.write(text)

    fin.close()
    fout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Tweets')
    parser.add_argument('--inputdir', '-i', help='Input Dir')
    args = parser.parse_args()

    extractTweets(args.inputdir)
