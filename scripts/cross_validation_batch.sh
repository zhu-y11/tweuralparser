#!/bin/bash

for j in 0 1 2 3 4 5 6 7 8 9
  do
    echo "Running fold ${j} ..."
    ./examples/dp-parser --fold $j --dynet-seed 1234 --script_filepath ../../StackLSTM/scripts/ --model ./model/ --pretrained_model ./model_epoch_15 --training_data ../../StackLSTM/data/tweet/cross_validation/cross_train_allproj_$j --dev_data ../../StackLSTM/data/tweet/cross_validation/cross_dev_autopos_$j  --test_data ../../StackLSTM/data/tweet/cross_validation/cross_dev_autopos_$j --use_pos_tags --rel_dim 8 --action_dim 8 --dynet-weight-decay 1e-5 --pretrained_embedding_filepath ~/glove.twitter.27B.100d.txt --char_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/char_set --pos_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/pos_set --action_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/action_set > outputs_$j 2>&1
  done
