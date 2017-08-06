# -*- coding: UTF-8 -*-
#!/usr/bin/python
"""
Convert parsing result to conll format for TWEET
@Author Yi Zhu
Upated 01/30/2017
"""

#************************************************************
# Imported Libraries
#************************************************************
import argparse


#************************************************************
# Global Variables
#************************************************************


def convet2CONLL(input_file, output_file):
    fout = open(output_file, 'wb')
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            dp_map = {}
            dp_stack = []
            split_idx = line.find(' ||| ')
            sent = line[:split_idx].strip()
            ops = line[split_idx + 5:].strip().split()
            dp_buffer = sent.split()
            dp_buffer = [[i, b[:b.rfind('/')], b[b.rfind('/') + 1:]] for i, b in enumerate(dp_buffer)]
            for op_pair in ops:
                if op_pair == 'SHIFT':
                    dp_stack.append(dp_buffer.pop(0))
                elif op_pair == 'SKIP':
                    word = dp_buffer.pop(0)
                    dp_map[word[0]] = '%d\t%s\t_\t%s\t%s\t_\t%d\t_\t_\t_'%(word[0], word[1], word[-1], word[-1], -3)
                else:
                    s_idx = op_pair.rfind('/')
                    op = op_pair[:s_idx]
                    rel = op_pair[s_idx + 1:]
                    if op == 'LEFT_ARC':
                        mod = dp_stack[-2]
                        head = dp_stack[-1]
                        dp_map[mod[0]] = '%d\t%s\t_\t%s\t%s\t_\t%d\t%s\t_\t_'%(mod[0], mod[1], mod[-1], mod[-1], head[0], rel)
                        dp_stack.pop(-2)
                    elif op == 'RIGHT_ARC':
                        mod = dp_stack[-1]
                        head = dp_stack[-2]
                        dp_map[mod[0]] = '%d\t%s\t_\t%s\t%s\t_\t%d\t%s\t_\t_'%(mod[0], mod[1], mod[-1], mod[-1], head[0], rel)
                        dp_stack.pop()

            for i in sorted(dp_map.keys()):
                fout.write(dp_map[i] + '\n')
            fout.write('\n')

    fout.close()




if __name__ == '__main__':
    parser = argparse.ArgumentParser("CONLL format converter")
    parser.add_argument("--input", "-i", help = "input file", required = True) 
    parser.add_argument("--output", "-o", help = "converted output file", required = True) 
    args = parser.parse_args()
    convet2CONLL(args.input, args.output)
