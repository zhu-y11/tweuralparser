# -*- coding: UTF-8 -*-
#!/usr/bin/python3
"""
add Brown clusters to CONLL format
@Author Yi Zhu
Upated 06/08/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse


def add_br_clusters(input_file, cluster_file):
  word_clusters = open(cluster_file, 'r').read().split('\n')
  word_clusters = [w.split() for w in word_clusters if w]
  word_clusters = {w[1]: w[0] for w in word_clusters}
  tweets = [tweet.strip().split('\n') for tweet in open(input_file, 'r').read().strip().split('\n\n')]
  tweets = [[line.strip().split() for line in tweet] for tweet in tweets]
  for i, tweet in enumerate(tweets):
    for j, line in enumerate(tweet):
      if line[1].lower() in word_clusters:
        br_full = word_clusters[line[1].lower()]
        br_6 = br_full[:6]
        br_4 = br_full[:4]
      else:
        br_full = 'OOV'
        br_6 = 'OOV'
        br_4 = 'OOV'
      tweets[i][j] = tweets[i][j] + [br_4, br_6, br_full]
      print('\t'.join(tweets[i][j]))
    print()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description = 'Add Brown clusters to CONLL')
  parser.add_argument('input_file', help='input CONLL file')
  parser.add_argument('cluster_file', help='word cluster file')
  args = parser.parse_args()

  add_br_clusters(args.input_file, args.cluster_file)
