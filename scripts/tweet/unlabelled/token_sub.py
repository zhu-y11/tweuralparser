#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token substitution for lines of tweets of CONLL format
@Author Yijia Liu, Yi Zhu
Upated 03/31/2017
"""
import re
import sys
import codecs
import argparse

eyes = "[8:=;]"
nose = "['`\-]?"

URL = re.compile("https?:\/\/(\S+|www\.(\w+\.)+\S*)")
USER = re.compile("@\w+")
SMILE = re.compile("{0}{1}[)d]+|[)d]+{1}{0}".format(eyes, nose))
LOLFACE = re.compile("{0}{1}p+".format(eyes, nose))
SADFACE = re.compile("{0}{1}\(+|\)+{1}{0}".format(eyes, nose))
NEUTRALFACE = re.compile("{0}{1}[\/|l*]".format(eyes, nose))
HEART = re.compile("<3")
NUMBER = re.compile("^[-+]?[.\d]*[\d]+[:,.\d]*$")
HASHTAG = re.compile("#\S+")
REPEAT = re.compile("([!?.]){2,}")
ELONG = re.compile(r"(\S*?)(\w)\2{2,}")

def _hashtag(m):
	hashtag_body = m.group(0)[1:]
	if hashtag_body.upper() == hashtag_body:
		result = "{0}".format(hashtag_body)
	else:
		result = "{0}".format("_".join(re.sub(r"([A-Z])", r" \1", hashtag_body).split()))
	return result

def _repeat(m):
	return "{0}".format(m.group(1))

def _elong(m):
	return "{0}{1}".format(m.group(1), m.group(2))

regexs = [
	(URL, "<URL>"),
	(USER, "<USER>"),
	(SMILE, "<SMILE>"),
	(LOLFACE, "<LOLFACE>"),
	(SADFACE, "<SADFACE>"),
	(NEUTRALFACE, "<NEUTRALFACE>"),
	(HEART, "<HEART>"),
	(NUMBER, "<NUMBER>"),
	(HASHTAG, _hashtag),
	(REPEAT, _repeat),
	(ELONG, _elong)
]

def tok(inputf, form):
    if form == 'txt':
        with codecs.open(inputf, 'r', 'utf-8') as f:
            for line in f:
                line = tokenize(line)
                if line:
                    print(line)
    else:
        with codecs.open(inputf, 'r', 'utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    print()
                    continue
                linevec = line.strip().split(u'\t')
                linevec[1] = tokenize(linevec[1])
                print(u'\t'.join(linevec))


def tokenize(txt):
    txt = txt.strip()
    '''
    if codecs.utf_8_decode(txt)[0][-1] == u'…':
        return ''
    '''
    for regex, repl in regexs:
        txt = regex.sub(repl, txt)
    return txt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Token Substitution')
    parser.add_argument('inputf', help='input file')
    parser.add_argument('--format', '-f', required = True, choices = {'conll', 'txt'}, 
            help='the format of the input file')    

    args = parser.parse_args()
    tok(args.inputf, args.format)
