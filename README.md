nohup ./examples/dp-parser --dynet-seed 1234 --script_filepath ../../StackLSTM/scripts/ --model ./model/ --training_data ../../StackLSTM/data/tweet_train_allproj --dev_data ../../StackLSTM/data/tweet_dev --test_data ../../StackLSTM/data/tweet_test_autopos --use_pos_tags --use_brown_clusters --layers 1 --word_input_dim 16 --lstm_char_output_dim 16 --hidden_dim 56 --action_dim 16 --lstm_input_dim 25 --rel_dim 16 --dynet-weight-decay 1e-5 --pretrained_dim 100 --pretrained_embedding_filepath ~/glove.twitter.27B.100d.txt > outputs 2>&1 &

## Train PTB
nohup ./examples/dp-parser --save_model --dynet-seed 1234 --script_filepath ../../StackLSTM/scripts/ --model ./model/ --training_data 3 --dev_data 4 --test_data 5 --use_pos_tags  --rel_dim 8 --action_dim 8 --dynet-weight-decay 1e-5 --pretrained_embedding_filepath ~/sskip.100.vectors --files ../../StackLSTM/data/tweet/brown_cluster/tweet_train_subtoken_allproj ../../StackLSTM/data/tweet/brown_cluster/tweet_dev_subtoken_autopos ../../StackLSTM/data/tweet/brown_cluster/tweet_test_subtoken_autopos ../../StackLSTM/data/ym_ptb_train_tweetpos_norel ../../StackLSTM/data/ym_ptb_dev_tweetpos_norel ../../StackLSTM/data/ym_ptb_test_tweetpos_norel > outputs 2>&1 &


## Train Tweet
nohup ./examples/dp-parser --dynet-seed 1234 --script_filepath ../../StackLSTM/scripts/ --model ./model/ --pretrained_model model_epoch_4 --training_data 0 --dev_data 1 --test_data 2 --use_pos_tags --use_brown_clusters --rel_dim 8 --action_dim 8 --dynet-weight-decay 1e-5 --pretrained_embedding_filepath ~/sskip.100.vectors --files ../../StackLSTM/data/tweet/brown_cluster/tweet_train_subtoken_allproj ../../StackLSTM/data/tweet/brown_cluster/tweet_dev_subtoken_autopos ../../StackLSTM/data/tweet/brown_cluster/tweet_test_subtoken_autopos ../../StackLSTM/data/ym_ptb_train_tweetpos_norel ../../StackLSTM/data/ym_ptb_dev_tweetpos_norel ../../StackLSTM/data/ym_ptb_test_tweetpos_norel > outputs 2>&1 &


# Tritraining

## Train PTB
nohup ./examples/dp-parser --save_model \ 
--dynet-seed 1234 \
--script_filepath ../../StackLSTM/scripts/ \
--model ./model/ \
--training_data ../../StackLSTM/data/gfl_train_allproj \
--dev_data ../../StackLSTM/data/tweet/tweet_test \
--test_data ../../StackLSTM/data/tweet/tweet_test \  
--action_dim 8 \
--dynet-weight-decay 1e-5 \
--pretrained_embedding_filepath ~/glove.twitter.27B.100d.txt \
--char_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/char_set \
--pos_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/pos_set \
--action_set_filepath ../../StackLSTM/scripts/tweet/unlabelled/action_set \
--use_pos_tags --rel_dim 8 > outputs 2>&1 &
