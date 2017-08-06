import argparse
import codecs
import os
import re
import sys

parser = argparse.ArgumentParser(description='')
parser.add_argument('inputf', type=str, metavar='', help='intput file')

A = parser.parse_args()

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

from itertools import izip

def end_state(stack, input_buffer, action_history):
    if len(input_buffer) == 0 and len(stack) == 1 and stack[0] == 0:
        return True
    return False
        
def perform_action(stack, input_buffer, action, predicted_arcs):
    if action.startswith('SHIFT'):
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
    if len(stack) >= 2:
        # check if the top 2 arcs can be reduced
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
            if a1[0] > a2[0]:
                a1, a2 = a2, a1
            if a1[1] > a2[0] and a1[1] < a2[1] and a1[0] < a2[0]:
                # print a1, a2
                return False
    return True

def convert_sentence(sent, use_pos=True):
    words = [w[1] for w in sent]
    words.insert(0, "<ROOT>")
    poss = [w[3] for w in sent]
    poss.insert(0, "<ROOT>")
    
    lh = ""
    if use_pos:
        lh = " ".join(["/".join(w) for w in izip(words, poss)])
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
        return None
    labels = [w[7] for w in sent]
    label_dict = dict()
    for i in xrange(1, sent_len):
        label_dict[(parents[i], i)] = labels[i-1]
        
    actions = extract_actions(arcs, sent_len, True, label_dict)
    # print actions
    rh = " ".join(actions)
    return lh + " ||| " + rh

if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

    corpus = read_corpus(A.inputf)
    sys.stderr.write(str(len(corpus)) + "\n")

    for i in xrange(0, len(corpus)):
        res = convert_sentence(corpus[i])
        if res != None:
            print res
        else:
            sys.stderr.write("skip sentence " + str(i) + "\n")
