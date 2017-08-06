# Lingpeng Kong, lingpenk@cs.cmu.edu
# Jan 2, 2014

import sys


def usage():
    print "Usage: python PTBPOSTag2TwitterTag.py [Input Conll File] > [Output_file]"

tagdict = {
    "NN"   :  "N",
    "NNS"  :  "N",
    "WH"   :  "O",
    "PRP"  :  "O",
    "WP"   :  "O",
    "POS"  :  "S",
    "NNP"  :  "^",
    "NNPS" :  "^",
    "VB"   :  "V",
    "VBD"  :  "V",
    "VBG"  :  "V",
    "VBN"  :  "V",
    "VBP"  :  "V",
    "VBZ"  :  "V",
    "UH"   :  "!",
    "MD"   :  "V",
    "RB"   :  "R",
    "RBR"  :  "R",
    "RBS"  :  "R",
    "WRB"  :  "R",
    "WDT"  :  "D",
    "DT"   :  "D",
    "WP$"  :  "D",
    "PRP$" :  "D",
    "JJ"   :  "A",
    "JJR"  :  "A",
    "JJS"  :  "A",
    "IN"   :  "P",
    "TO"   :  "P",
    "CC"   :  "&",
    "RP"   :  "T",
    "EX"   :  "X",
    "PDT"  :  "X",
    "CD"   :  "$",
    "#"    :  ",",
    "$"    :  ",",
    "''"   :  ",",
    "``"   :  ",",
    "("    :  ",",
    ")"    :  ",",
    ","    :  ",",
    "."    :  ",",
    ":"    :  ",",
    "FW"   :  "G",
    "SYM"  :  "G",
    "LS"   :  "G",
    "%"    :  ","
}

def convert_line(cl):
    ptbtag = cl[3]
    twittertag = tagdict[ptbtag]

    ori_word = cl[1];
    if ori_word.lower() == "rt":
        twittertag = "~"
    if ori_word.lower() == "username":
        twittertag = "@"
    if ori_word.lower() == "urlname":
        twittertag = "U"

    #if twittertag == None:
    #    print ptbtag[4]
    #    exit()
    cl[4] = twittertag 
    cl[3] = twittertag
    return cl

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        sys.exit(2)
    inputf = sys.argv[1].strip()
    words = []
    for line in open(inputf, "r"):
        line = line.strip()
        if line == "":
            sys.stdout.write("\n")
            continue
        cvlist = convert_line(line.split("\t"))
        tline = ""
        for ele in cvlist:
            tline = tline + ele + "\t"
        tline = tline[:len(tline)-1]
        print tline
