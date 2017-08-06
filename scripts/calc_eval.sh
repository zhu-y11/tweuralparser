#!/bin/bash
if [ $# -ne 2 ]
then
  echo "Usage: $0 gold_standard_path sys_file_path"
  exit -1
fi

gold=$1
sysfile=$2
gold_conv="${gold}_conv"

+DIR=$(dirname "$0")

python $DIR/conll_converter.py -i $sysfile -o "${sysfile}_conv"
perl $DIR/eval.pl -q -g $gold_conv -s "${sysfile}_conv" | python $DIR/eval_parses.py 
