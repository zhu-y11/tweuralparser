#!/bin/bash
if [ $# -ne 2 ]
then
  echo "Usage: $0 gold_standard_path sys_file_path"
  exit -1
fi

gold=$1
sysfile=$2
gold_conv="${gold}_conv"

#DIR="$(pwd)"
DIR=$(dirname "$0")
#echo "$DIR"

python $DIR/tweet_conll_converter.py -i $sysfile -o "${sysfile}_conv"
python $DIR/MyEval_WithoutMWE.py $gold_conv "${sysfile}_conv"
