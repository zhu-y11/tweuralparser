# -*- coding: UTF-8 -*-
#!/usr/bin/python3
"""
Batch Running for TweeboParser
@Author Yi Zhu
Upated 03/20/2017
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


def runTweeboBatch(tweebopath, input_dir):
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if not f.endswith('.tok'):
                continue
            input_file = os.path.join(root, f)
            LOG.info('Processing {} ... '.format(input_file))
            tweebo_cmd = os.path.join(os.path.abspath(tweebopath), 'run.sh')
            cmd = [tweebo_cmd, input_file]
            call(cmd)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Batch Running for TweeboParser')
    parser.add_argument('tweebopath', help='TweeboParser Path')
    parser.add_argument('inputdir', help='Input Dir')
    A = parser.parse_args()
    
    runTweeboBatch(A.tweebopath, A.inputdir)

