# -*- coding: UTF-8 -*-
#!/usr/bin/python
"""
Convert CONLL to Seq for both training and testing data
@Author Yi Zhu
Upated 02/10/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse
import codecs
import os
import re
import sys
from itertools import izip
from subprocess import call


def read_corpus(filename):
    f = codecs.open(filename, "r", "utf-8")
    corpus = []
    sentence = []
    for line in f:
        if line.strip() == "":
            corpus.append(sentence)
            sentence = []
            continue
        else:
            line = line.strip()
            cline = line.split(u"\t")
            sentence.append(cline)
    f.close()
    return corpus


def done_with_right_children(stack_top, input_buffer, arcs):
    for i in input_buffer:
        if (stack_top, i) in arcs:
            return False
    return True


def end_state(stack, input_buffer, action_history):
    if len(input_buffer) == 0 and len(stack) == 1 and stack[0] == 0:
        return True
    return False
        

def perform_action(stack, input_buffer, action, predicted_arcs):
    if action.startswith('SKIP'):
        assert(input_buffer > 0)
        predicted_arcs.append((-3, input_buffer[-1]))
        input_buffer.pop()
    elif action.startswith('SHIFT'):
        assert(input_buffer > 0)
        stack.append(input_buffer[-1])
        input_buffer.pop()        
    elif action.startswith('LEFT_ARC'):
        assert(len(stack) >= 2)
        predicted_arcs.append((stack[-1], stack[-2]))
        head = stack[-1]
        stack.pop()
        stack.pop()
        stack.append(head)
    elif action.startswith('RIGHT_ARC'):
        assert(len(stack) >= 2)
        predicted_arcs.append((stack[-2], stack[-1]))
        head = stack[-2]
        stack.pop()
        stack.pop()
        stack.append(head)
    else:
        assert(False)
        

def get_gold_action(stack, input_buffer, action_history, arcs, enable_label = False, label_dict = None):
    # print stack
    # print input_buffer
    if input_buffer:
        buffer_top_skip = (-3, input_buffer[-1])
        if buffer_top_skip in arcs:
            return 'SKIP'

    if len(stack) >= 2:
        # check if the top 2 arcs can be reduced
        # parent -> child
        top2_l = (stack[-1], stack[-2])
        top2_r = (stack[-2], stack[-1])
        if top2_r in arcs:
            if done_with_right_children(stack[-1], input_buffer, arcs):
                return 'RIGHT_ARC' + '/' + label_dict[(top2_r)] if enable_label else 'RIGHT_ARC'
            else:
                return 'SHIFT'
        elif top2_l in arcs:
            return 'LEFT_ARC' + '/' + label_dict[(top2_l)] if enable_label else 'LEFT_ARC'
        else:
            return 'SHIFT'
    else:
        return 'SHIFT'


def extract_actions(arcs, sent_len, enable_label = False, label_dict = None):
    # stack, input, action
    # set up the initial state
    
    # at first the stack is empty
    stack = []
    input_buffer = range(sent_len)
    input_buffer.reverse()
    action_history = []
    predicted_arcs = []
    
    while not end_state(stack, input_buffer, action_history):
        action = get_gold_action(stack, input_buffer, action_history, arcs, enable_label, label_dict)
        
        # print action
        perform_action(stack, input_buffer, action, predicted_arcs)
        
        action_history.append(action)
    assert(set(predicted_arcs) == arcs)
    return action_history


def is_projective(arcs):
    for i in xrange(len(arcs)):
        for j in xrange(len(arcs)):
            if i < j:
                continue
            a1 = list(arcs[i])
            a2 = list(arcs[j])
            a1.sort()
            a2.sort()
            if a1[0] == -3 or a2[0] == -3:
                continue
            if a1[0] > a2[0]:
                a1, a2 = a2, a1
            if a1[1] > a2[0] and a1[1] < a2[1] and a1[0] < a2[0]:
                # print a1, a2
                return False
    return True


def convert_sentence(sent, use_pos = True, use_brown = False):
    # Add root to word sequence and pos sequence
    words = [w[1] for w in sent]
    words.insert(0, "<ROOT>")
    poss = [w[3] for w in sent]
    poss.insert(0, "<ROOT>")

    if use_brown:
        br4 = [w[10] for w in sent]
        br4.insert(0, '<ROOT>')
        br6 = [w[11] for w in sent]
        br6.insert(0, '<ROOT>')
        brall = [w[12] for w in sent]
        brall.insert(0, '<ROOT>')
    
    # Raw word/pos sequence
    lh = ""
    if use_pos and use_brown:
        lh = " ".join(["/".join(w) for w in izip(words, poss, br4, br6, brall)])
    elif use_pos:
        lh = " ".join(["/".join(w) for w in izip(words, poss)])
    elif use_brown:
        lh = " ".join(["/".join(w) for w in izip(words, br4, br6, brall)])
    else:
        lh = " ".join(words)
    #print lh
    
    parents = [int(w[6]) for w in sent]
    
    # add one for the root 0
    sent_len = len(parents) + 1
    parents.insert(0, 0)
    
    # 0 is the root
    # (parent, child) is the arc
    arcs = set([(parents[i], i) for i in range(1, sent_len)])
    arc_list = list(arcs)
    #print "**" + str(is_projective(arc_list))
    if not is_projective(arc_list):
        return lh + ' ||| '

    labels = [w[7] for w in sent]

    label_dict = dict()
    for i in xrange(1, sent_len):
        label_dict[(parents[i], i)] = labels[i-1]
        
    actions = extract_actions(arcs, sent_len, True, label_dict)
    # print actions
    rh = " ".join(actions)
    return lh + " ||| " + rh


def convertCorpus(conll_in, seq_out, conll_out, mode, np2p, autopos, use_pos, use_brown):
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

    corpus = read_corpus(conll_in)
    sys.stderr.write('{} sentences in the input file\n'.format(len(corpus)))
    out_ct = None

    if mode == 'train':
        if np2p:
            sys.stderr.write('Converting training data {} ... \nTransforming non-projective sentences to projective sentences ... \n'.format(conll_in))
            out_ct = trainNp2p(corpus, seq_out, conll_out, use_pos, use_brown)
        else:
            sys.stderr.write('Converting training data {} ... \nDiscarding non-projective sentences ... \n'.format(conll_in))
            out_ct = trainDiscardNp(corpus, seq_out, conll_out, sys.stderr, use_pos, use_brown)
    else:
        if autopos:
            sys.stderr.write('Converting training data {} ... \nUsing automatic POS ... \n'.format(conll_in))
            out_ct = testAutoPos(corpus, seq_out, conll_out, use_pos, use_brown)
        else:
            sys.stderr.write('Converting training data {} ... \nUsing gold POS ... \n'.format(conll_in))
            out_ct = testGoldPos(corpus, seq_out, conll_out, use_pos, use_brown)
    sys.stderr.write('{} sentences in the output file\n'.format(out_ct))


def trainNp2p(corpus, seq_out, conll_out, use_pos, use_brown):
    fout_seq = codecs.open(seq_out, "w", "utf-8")
    fout_conll = codecs.open(conll_out, "w", "utf-8")
    fout_conll_tp = codecs.open('train_nonproj', 'w', 'utf-8')
    out_ct = 0
    for i, sent in enumerate(corpus):
        res = convert_sentence(sent, use_pos, use_brown)
        # Training, non-projective sentences 2 pseudo projective sentences
        if res.endswith(' ||| '):
            # non-proj sent
            sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
            fout_conll_tp.write(sent_conll)
            out_ct += 1
        else:
            fout_seq.write(res + u"\n")
            sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
            fout_conll.write(sent_conll)
            out_ct += 1

    fout_conll_tp.close()
    fout_conll_tp = codecs.open('train_nonproj_ts', 'w', 'utf-8')
    nonproj_corps = read_corpus('train_nonproj')
    for i, sent in enumerate(nonproj_corps):
        new_line = []
        for line in sent:
            if line[6] == u'-3':
                continue
            new_line.append(line)
        idx_map = {}
        j = 1
        for line in new_line:
            idx_map[line[0]] = j
            j += 1
        for line in new_line:
            line[0] = str(idx_map[line[0]])
            line[6] = str(idx_map[line[6]]) if line[6] != u'0' else u'0'
        sent_conll = u"\n".join([u"\t".join(line) for line in new_line]) + u"\n\n"
        fout_conll_tp.write(sent_conll) 
    fout_conll_tp.close()
    call(['java', '-jar', 'maltparser-1.8.1/maltparser-1.8.1.jar', '-c', 'pproj', '-m', 'proj', '-i', 'train_nonproj_ts', '-o', 'train_proj_ts', '-pp', 'baseline'])

    with codecs.open('train_proj', 'w', 'utf-8') as f:
        sents = read_corpus('train_nonproj')  
        sents_ts = read_corpus('train_proj_ts') 
        assert len(sents) == len(sents_ts)

        for i in xrange(len(sents)):
            idx_map = {}
            idx_inv_map = {'0':'0'}
            k = 0
            for j, line in enumerate(sents[i]):
                if int(line[6]) == -3:
                    continue

                if line[1] == sents_ts[i][k][1]:
                    idx_map[j] = k
                    idx_inv_map[str(k + 1)] = str(j + 1)
                    k += 1
                else:
                    print 'ERROR!!'
                    sys.exit(1)

            for j, line in enumerate(sents[i]):
                if int(line[6]) == -3:
                    continue
                if int(line[6]) != 0:
                    line[6] = idx_inv_map[sents_ts[i][idx_map[j]][6]]

            sent = u"\n".join([u"\t".join(line) for line in sents[i]]) + u"\n\n"
            f.write(sent)

    proj_corps = read_corpus('train_proj')
    for i, sent in enumerate(proj_corps):
        res = convert_sentence(sent, use_pos, use_brown)
        fout_seq.write(res + u"\n")
        sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
        fout_conll.write(sent_conll) 

    fout_seq.close()
    fout_conll.close()
    os.remove('train_nonproj')
    os.remove('train_nonproj_ts')
    os.remove('train_proj')
    os.remove('train_proj_ts')
    return out_ct


def trainDiscardNp(corpus, seq_out, conll_out, stderr, use_pos, use_brown):
    fout_seq = codecs.open(seq_out, "w", "utf-8")
    fout_conll = codecs.open(conll_out, "w", "utf-8")
    out_ct = 0
    for i, sent in enumerate(corpus):
        res = convert_sentence(sent, use_pos, use_brown)
        # Training, discard non-projective sentences
        if res.endswith(' ||| '):
            # non-proj sent
            stderr.write("skip sentence " + str(i) + "\n")
        else:
            fout_seq.write(res + u"\n")
            sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
            fout_conll.write(sent_conll)
            out_ct += 1

    fout_seq.close()
    fout_conll.close()
    return out_ct



def testAutoPos(corpus, seq_out, conll_out, use_pos, use_brown):
    fout_seq = codecs.open(seq_out, "w", "utf-8")
    fout_conll = codecs.open(conll_out, "w", "utf-8")
    fout_conll_tp = codecs.open('gold_pos', 'w', 'utf-8')
    out_ct = 0
    for i, sent in enumerate(corpus):
        res = convert_sentence(sent, use_pos, use_brown)
        # Testing, automatic POS tags
        sent_conll = u"\n".join([u"\t".join([line[1], line[3]]) for line in sent]) + u"\n\n"
        fout_conll_tp.write(sent_conll)
        out_ct += 1

    with open('pred_pos', 'w') as f:
        call(['./runTagger.sh', '--input-format', 'conll', '--output-format', 'conll', 
            '--model', 'pretrained_models/tagging_model', 'gold_pos'], stdout = f)
    word_pos = read_corpus('pred_pos')
    for i, sent in enumerate(corpus):
        assert len(sent) == len(word_pos[i])
        for j, word in enumerate(sent):
            assert sent[j][1] == word_pos[i][j][0]
            sent[j][3] = word_pos[i][j][1]
            sent[j][4] = word_pos[i][j][1]
        res = convert_sentence(sent, use_pos, use_brown)
        fout_seq.write(res + u"\n")
        sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
        fout_conll.write(sent_conll)
    os.remove('pred_pos')
    os.remove('gold_pos')

    fout_seq.close()
    fout_conll.close()
    return out_ct


def testGoldPos(corpus, seq_out, conll_out, use_pos, use_brown):
    fout_seq = codecs.open(seq_out, "w", "utf-8")
    fout_conll = codecs.open(conll_out, "w", "utf-8")
    out_ct = 0
    for i, sent in enumerate(corpus):
        res = convert_sentence(sent, use_pos, use_brown)
        # Testing, gold POS tags
        fout_seq.write(res + u"\n")
        sent_conll = u"\n".join([u"\t".join(line) for line in sent]) + u"\n\n"
        fout_conll.write(sent_conll)
        out_ct += 1

    fout_seq.close()
    fout_conll.close()
    return out_ct


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Original CONLL Tweebank to transition seq & CONLL format')
    parser.add_argument('inputf', help='CONLL original input file')
    parser.add_argument('outputf', help='TRANSITION output file')
    parser.add_argument('output_conv', help='CONLL output file')
    parser.add_argument('-m','--mode', help='mode: trainining data or testing data', default = 'train', choices = {'train', 'test'})
    parser.add_argument('-np2p','--nonproj2pro', type = int, help = 'non projective sentences -> projective sentences', default = 1, choices = {0, 1})
    parser.add_argument('-autopos','--autopos', type = int, help='', default = 0, choices = {0, 1})
    parser.add_argument('-pos','--use_pos', type = int, help='', default = 1, choices = {0, 1})
    parser.add_argument('-br','--use_brown', type = int, help='', default = 0, choices = {0, 1})

    A = parser.parse_args()

    convertCorpus(A.inputf, A.outputf, A.output_conv, A.mode, A.nonproj2pro, A.autopos, A.use_pos, A.use_brown)
