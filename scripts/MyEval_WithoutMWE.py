import argparse
import codecs
import os
import re
import sys

parser = argparse.ArgumentParser(description='Conll')
parser.add_argument('gold', type=str, metavar='', help='gold file')
parser.add_argument('system', type=str, metavar='', help='system file')
A = parser.parse_args()

def make_sentence_unique(sent):
	for i in xrange(0, len(sent)):
		time = 0
		for j in xrange(0, i):
			if sent[j] == sent[i]:
				time += 1
		sent[i] = sent[i] + ("+++" + str(time) if time > 0 else "")


def eval_sentence(sentsys, sentgold):
  
  total_mwe_num = 0
  sysparent, systokens, sysindex = [], [], {}
  i = 0
  for line in sentsys:
    f = line.split(u'\t')
    if int(f[6]) < 0: continue
    sysparent.append(int(f[6]))
    sysindex[int(f[0])] = i
    i += 1
    systokens.append(f[1])
  #end for

  goldparent, goldtokens, goldmwe, goldindex = [], [], [], {}

  i = 0
  for line in sentgold:
    f = line.split(u'\t')
    if int(f[6]) < 0: continue
    goldparent.append(int(f[6]))
    goldtokens.append(f[1])
    goldmwe.append(f[7] == u'MWE')
    goldindex[int(f[0])] = i
    i += 1
  #end for

  # print zip(goldtokens, goldmwe)
  # print sysindex

  sysN, goldN = len(systokens), len(goldtokens)

  goldmwe_cluster = [[] for i in xrange(goldN)]

  make_sentence_unique(goldtokens)
  make_sentence_unique(systokens)

  for tok, parent, mwe, i in zip(goldtokens, goldparent, goldmwe, xrange(goldN)):
    if mwe:
      found = False
      for cluster in goldmwe_cluster:
        if goldtokens[goldindex[parent]] in cluster:
          cluster.append(tok)
          found = True
          break
        #end if
      #end for
      if not found:
        goldmwe_cluster[goldindex[parent]].append(tok)
    else:
      goldmwe_cluster[i].append(tok)
    #end if
  #end for
  total_mwe_num += len(filter(lambda x: len(x) > 1, goldmwe_cluster))


  for i in xrange(goldN):
    if len(goldmwe_cluster[i]) == 0:
      for j in xrange(goldN):
        if goldtokens[i] in goldmwe_cluster[j]:
          goldmwe_cluster[i] = list(goldmwe_cluster[j])
          break
        #end if
      #end for
    #end if
  #end for

  sysmwe_cluster = [[] for i in xrange(sysN)]
  for i in xrange(sysN):
    found = False
    for j in xrange(goldN):
      if systokens[i] in goldmwe_cluster[j]:
        sysmwe_cluster[i] = goldmwe_cluster[j]
        found = True
        break
      #end if
    #end for
    if not found:
      sysmwe_cluster[i] = [systokens[i]]
  #end for

  # print sysmwe_cluster, goldmwe_cluster

  sysdeps = set()
  for i in xrange(sysN):
    cluster_i = u'-'.join(sysmwe_cluster[i])
    if sysparent[i] not in sysindex:
      continue
    elif sysparent[i] == 0:
      sysdeps.add(cluster_i + u'->__ROOT__')
    else:
      k = sysindex[sysparent[i]]
      cluster_k = u'-'.join(sysmwe_cluster[k])
      # print u'-'.join(sysmwe_cluster[i]) + u'->' + u'-'.join(sysmwe_cluster[k])
      if cluster_i != cluster_k: sysdeps.add(cluster_i + u'->' + cluster_k)
    #end if
  #end for
  # print u'\n'.join(sysdeps)

  golddeps = set()
  for i in xrange(goldN):
    cluster_i = u'-'.join(goldmwe_cluster[i])
    if goldparent[i] not in goldindex:
      continue
    elif goldparent[i] == 0:
      golddeps.add(cluster_i + u'->__ROOT__')
    else:
      k = goldindex[goldparent[i]]
      cluster_k = u'-'.join(goldmwe_cluster[k])
      # print u'-'.join(goldmwe_cluster[i]) + u'->' + u'-'.join(goldmwe_cluster[k])
      if cluster_i != cluster_k: golddeps.add(cluster_i + u'->' + cluster_k)
    #end if
  #end for

  correct = float(len(set(sysdeps & golddeps)))
  precision, recall = 0, 0
  # precision = cqect / len(golddeps)
  return correct, len(sysdeps), len(golddeps), total_mwe_num
#end def

if __name__ == '__main__':
  sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
  sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

  g = codecs.open(A.gold, 'r', 'utf-8')
  f = codecs.open(A.system, 'r', 'utf-8')
  

  syslines = f.readlines()
  goldlines = g.readlines()
  i, j = 0, 0

  total_correct, total_sys, total_gold, total_mwe = 0, 0, 0, 0

  while True:
    if syslines[i].strip() != '':
      i += 1
    if goldlines[j].strip() != '':
      j += 1

    if goldlines[j].strip() == '' and syslines[i].strip() == '':
      correct, sys_count, gold_count, num_mwe = eval_sentence(syslines[:i], goldlines[:j])
      total_correct += correct
      total_sys += sys_count
      total_gold += gold_count
      total_mwe += num_mwe

      syslines = syslines[i+1:]
      goldlines = goldlines[j+1:]
      i, j = 0, 0
    #end if
    if not goldlines and not syslines: break
  #end while

  #print float(total_correct), total_sys, total_gold
  precision = float(total_correct) / total_sys
  recall = float(total_correct) / total_gold
  #print float(total_correct) / total_sys
  #print float(total_correct) / total_gold
  print (2.0 * ( (precision * recall) / (precision + recall) ))
  #print total_mwe
#end if
