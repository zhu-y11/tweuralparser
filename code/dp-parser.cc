#include <cstdlib>
#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <chrono>
#include <ctime>
#include <unordered_set>
#include <unordered_map>

#include <execinfo.h>
#include <unistd.h>
#include <signal.h>

#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>
#include <boost/program_options.hpp>

#include "dynet/training.h"
#include "dynet/dynet.h"
#include "dynet/expr.h"
#include "dynet/nodes.h"
#include "dynet/lstm.h"
#include "dynet/rnn.h"
#include "dynet/dict.h"
#include "dynet/cfsm-builder.h"
#include "dynet/timing.h"
#include "dynet/globals.h"


#include "conll_reader.hpp"
#include "dict_map.hpp"


using namespace dynet::expr;
using namespace dynet;
using namespace std;

struct ModelVars
{
    public:
        bool USE_POS;
        unsigned LAYERS;
        unsigned CHAR_INPUT_DIM;
        unsigned WORD_INPUT_DIM;
        unsigned LSTM_CHAR_OUTPUT_DIM;
        unsigned HIDDEN_DIM;
        unsigned ACTION_DIM;
        unsigned PRETRAINED_DIM;
        unsigned LSTM_INPUT_DIM;
        unsigned POS_DIM;
        unsigned REL_DIM;
        bool USE_BROWN;
        bool SAVE_MODEL;

        string pretrained_embedding_filepath;
        string model_filepath;
        string pretrained_model;
        string char_set_filepath;
        string pos_set_filepath;
        string action_set_filepath;

        string to_string()
        {
            ostringstream os;
            os << "Model Vars:" << "\n"
            << "CHAR_INPUT_DIM: " << CHAR_INPUT_DIM << "\n"
            << "WORD_INPUT_DIM: " << WORD_INPUT_DIM << "\n"
            << "LSTM_CHAR_OUTPUT_DIM: " << LSTM_CHAR_OUTPUT_DIM << "\n"
            << "HIDDEN_DIM: " << HIDDEN_DIM << "\n"
            << "ACTION_DIM: " << ACTION_DIM << "\n"
            << "PRETRAINED_DIM: " << PRETRAINED_DIM << "\n"
            << "LSTM_INPUT_DIM: " << LSTM_INPUT_DIM << "\n"
            << "POS_DIM: " << POS_DIM << "\n"
            << "REL_DIM: " << REL_DIM << "\n"
            << "pretrained_embedding_filepath: " << pretrained_embedding_filepath << "\n"
            << "model_filepath: " << model_filepath << "\n"
            << "pretrained_model_filepath: " << pretrained_model << "\n"
            << "USE_POS: " << USE_POS << "\n"
            << "USE_BROWN: " << USE_BROWN << "\n"
            << "SAVE_MODEL: " << SAVE_MODEL << "\n"
            << "char_set_filepath: " << char_set_filepath << "\n"
            << "pos_set_filepath: " << pos_set_filepath << "\n"
            << "action_set_filepath: " << action_set_filepath << "\n";
            return os.str();
        }

        void counter_clean()
        {
            correct = 0.0;
            total = 0.0;
        }
    
        void counter_correct_plus_one()
        {
            correct = correct + 1;
        }
    
        void counter_total_plus_one()
        {
            total = total + 1;
        }
    
        float current_acc()
        {
            return (correct/total);
        }
    
    private:
        float correct = 0.0;
        float total = 0.0;
};

// A ParserState will not save any parameters
// And it will not take care of the parameter initialization
// It just perform the actions and maintain the logic of the transition system
// It should also don't store index in the dictionary. All the indice in this class
// will be refering to the position in the sentence.
// A DictMap pointer to the current dict_map will be stored in
class ParserState
{
    public:
        explicit ParserState(LSTMBuilder* stack_lstm, LSTMBuilder* buffer_lstm, LSTMBuilder* action_lstm,
                             unordered_map<string, Expression> *named_expressions, DictMap* dict_map, Sentence* sent) :
        stack_lstm_(stack_lstm),
        buffer_lstm_(buffer_lstm),
        action_lstm_(action_lstm),
        named_expressions_(named_expressions),
        dict_map_(dict_map),
        sent_(sent)
        {
            stack.clear();
            buffer.clear();
            actions.clear();
            stack_exp.clear();
            buffer_exp.clear();
        };

        ~ParserState(){};

        void perform_action(int action, Expression action_emb, Expression relation_emb)
        {
            //cout << "in perform_action()" << endl;
            //cout << "PERFORM ACTION: " << get_action_string(action) << endl;
            assert(is_valid_action(action));
            string action_str = get_action_string(action);
            if (action_str.compare("SHIFT") == 0)
            {
                // push to the stack and remove from the buffer
                stack_push(buffer_exp.back(), buffer.back());
                buffer_pop();
            }
            else if(action_str.compare("SKIP") == 0)
            {
                buffer_pop();
            }
            else
            {
                assert(action_str.compare("LEFT_ARC") == 0 || action_str.compare("RIGHT_ARC") == 0);
                // Determine the dep and head, pop two elements from the stack
                bool right_arc = (action_str.compare("RIGHT_ARC") == 0);
                //cout << "DEBUG:"<<right_arc << action_str<<endl;
                Expression dep, head;
                int depi, headi;
                /*
                 * right_arc:
                 * dep = stack_exp.back()
                 * depi = stack.back()
                 * stack_pop()
                 * head = stack_exp.back()
                 * headi = stack.back()
                 * stack_pop()
                 *
                 * left-arc:
                 * head = stack_exp.back()
                 * headi = stack.back()
                 * stack_pop()
                 * dep = stack_exp.back()
                 * depi = stack.back()
                 * stack_pop()
                 */
                (right_arc ? dep : head) = stack_exp.back();
                (right_arc ? depi : headi) = stack.back();
                stack_pop();
                (right_arc ? head : dep) = stack_exp.back();
                (right_arc ? headi : depi) = stack.back();
                stack_pop();

                // Compute the composition Expression
                // nlcompose = tanh(H* head + D * dep + R * relation_emb + cbias)
                Expression composed = affine_transform({named_expressions_->at("cbias"), named_expressions_->at("H"), head, named_expressions_->at("D"),
                                                        dep, named_expressions_->at("R"), relation_emb});
                /*
                 vector<float> debug_composed_value = as_vector(composed.pg->get_value(composed));
                 assert(debug_composed_value.size() == 50);
                 cout << debug_composed_value[48] << endl;
                 */
                Expression nlcomposed = tanh(composed);
      
                stack_push(nlcomposed, headi);
            }
            action_lstm_->add_input(action_emb);
        }

        bool is_valid_action(int action)
        {
            //cout << "is_valid_action: " << buffer.size() << " " << stack.size() << endl;
            string action_str = get_action_string(action);
            //cout << "is_valid_action: " << action_str << endl;
            if (action_str.compare("SHIFT") == 0 || action_str.compare("SKIP") == 0)
            {
                // Make sure there are still things on the buffer.
                if (!(buffer.size() > 1)) return false;
            }
            else
            {
                // guard, root plus one word has to be on the stack
                if (!(stack.size() > 2)) return false;
            }
            return true;
        }

        int next_action(const vector<float> &dist)
        {
            assert(dict_map_->action_size() == dist.size());
            int max = -1;
            float max_score = -std::numeric_limits<float>::infinity();
            for (int i = 0; i < static_cast<int>(dist.size()); i++)
            {
                if (!is_valid_action(i)) continue;
                if (dist[i] > max_score)
                {
                    max_score = dist[i];
                    //cout<< max_score << endl;
                    max = i;
                }
            }
      
            if (max == -1)
            {
                // None of the action is picked, print the log
                cerr << "buffer size: " << buffer.size() << endl;
                for (auto x : buffer)
                {
                    cerr << x << " ";
                }
                cerr << endl;
                cerr << "stack size: " << stack.size() << endl;
                for (auto x : stack)
                {
                    cerr << x << " ";
                }
                cerr << endl;
                for (auto x : dist)
                {
                    cerr << x << " ";
                }
                cerr << endl;
            }
            assert(max >= 0);
            return max;
        }

        // Note here we just init the state, not the parameters.
        void init(Expression& stack_guard, Expression& buffer_guard, Expression& action_guard)
        {
            // init lstm
            stack_lstm_->start_new_sequence();
            buffer_lstm_->start_new_sequence();
            action_lstm_->start_new_sequence();
            
            //vector<int>, pos in sentence
            stack.clear();
            buffer.clear();
            actions.clear();
            buffer_push(buffer_guard, -1);
            stack_push(stack_guard, -1);
            action_lstm_->add_input(action_guard);
        }

        void buffer_push(Expression& exp, int index)
        {
            //cout << "buffer size: " << buffer.size() << endl;
            buffer_lstm_->add_input(exp);
            buffer_exp.push_back(exp);
            buffer.push_back(index);
        }

        void buffer_pop()
        {
            buffer_lstm_->rewind_one_step();
            buffer_exp.pop_back();
            buffer.pop_back();
        }

        void stack_push(Expression& exp, int index)
        {
            stack_lstm_->add_input(exp);
            stack_exp.push_back(exp);
            stack.push_back(index);
        }

        void stack_pop()
        {
            stack_lstm_->rewind_one_step();
            stack_exp.pop_back();
            stack.pop_back();
        }

        bool is_end_state()
        {
            assert(buffer.size() > 0 && stack.size() > 0);
            // buffer.size() == 1 means only the guard is there.
            // stack.size() == 2 means only the guard and the root symbol is there.
            //cout << "DEBUG:END_STATE: " << ((buffer.size() == 1) && (stack.size() == 2)) << endl;
            return (buffer.size() == 1) && (stack.size() == 2);
        }

    public:
        // These index below should be the position in the sent
        vector<int> stack;
        vector<int> buffer;
        vector<int> actions;
        vector<Expression> stack_exp;
        vector<Expression> buffer_exp;
 
    private:
        bool is_valid_action()
        {
            return true;
        }

        string get_action_string(int action)
        {
            string action_str_w_label = (dict_map_->get_dict(DictMap::DICTMAP_IND_ACTION)).convert(action);
            string action_str = action_str_w_label.substr(0, action_str_w_label.rfind('/'));
            return action_str;
        }

        string get_relation_string(int action)
        {
            string action_str_w_label = (dict_map_->get_dict(DictMap::DICTMAP_IND_ACTION)).convert(action);
            auto split_pos = action_str_w_label.rfind('/');
            assert(split_pos != string::npos && split_pos + 1 < action_str_w_label.size());
            string relation_str = action_str_w_label.substr(split_pos + 1);
            return relation_str;
        }

    private:
        // The LSTMBuilders
        LSTMBuilder* stack_lstm_;
        LSTMBuilder* buffer_lstm_;
        LSTMBuilder* action_lstm_;

        unordered_map<string, Expression>* named_expressions_;
        DictMap* dict_map_;
        Sentence* sent_;
};

struct ParserBuilder
{
    explicit ParserBuilder(Model& model, Model& ns_model, ModelVars* mv, DictMap* dict_map):
    mv_(mv),
    dict_map_(dict_map),
    // Parameter for the LSTMs
    // LSTM_INPUT_DIM * 1
    p_stack_guard(model.add_parameters({mv_->LSTM_INPUT_DIM})),
    p_buffer_guard(model.add_parameters({mv_->LSTM_INPUT_DIM})),
    p_action_guard(model.add_parameters({mv_->ACTION_DIM})),
    
    // number of layers, input dimension, hidden dimension, model
    stack_lstm(mv_->LAYERS, mv_->LSTM_INPUT_DIM, mv_->HIDDEN_DIM, model),
    buffer_lstm(mv_->LAYERS, mv_->LSTM_INPUT_DIM, mv_->HIDDEN_DIM, model),
    action_lstm(mv_->LAYERS, mv_->ACTION_DIM, mv_->HIDDEN_DIM, model),
    
    // Parameter for the char-LSTMs
    p_start_of_word(model.add_parameters({mv_->CHAR_INPUT_DIM})),
    p_end_of_word(model.add_parameters({mv_->CHAR_INPUT_DIM})), 
    fw_char_lstm(mv_->LAYERS, mv_->CHAR_INPUT_DIM, mv_->LSTM_CHAR_OUTPUT_DIM, model),
    bw_char_lstm(mv_->LAYERS, mv_->CHAR_INPUT_DIM, mv_->LSTM_CHAR_OUTPUT_DIM, model),
    
    // Parameter for word, pretrained, and char
    // word embeddings
    //p_w(model.add_lookup_parameters(dict_map_->vocab_size(), {mv_->WORD_INPUT_DIM})),
    // the root representation in char lstm
    p_root_in_char(model.add_parameters({mv_->LSTM_CHAR_OUTPUT_DIM})),
    // lookup for chars
    p_c(model.add_lookup_parameters(dict_map_->char_size(), {mv_->CHAR_INPUT_DIM})),
    // pretrained word embeddings (not updated)
    p_t(ns_model.add_lookup_parameters(dict_map_->lc_vocab_size(), {mv_->PRETRAINED_DIM})),
    
    // Parameter for the concatenation of input, char_fwd, char_bwd, word, pos, pretrain
    p_x2i(model.add_parameters({mv_->LSTM_INPUT_DIM, (2 * mv_->LSTM_CHAR_OUTPUT_DIM + mv_->POS_DIM + mv_->PRETRAINED_DIM)})),
    p_x2ib(model.add_parameters({mv_->LSTM_INPUT_DIM})),
    
    // Parameter for action and relation lookup
    // action embeddings
    p_a(model.add_lookup_parameters(dict_map_->action_size(), {mv_->ACTION_DIM})),
    // realation embeddings
    p_r(model.add_lookup_parameters(dict_map_->action_size(), {mv_->REL_DIM})),
    
    // Parameter for the final prediction layer
    // combine the LSTMs
    // action lstm to parser state
    p_A(model.add_parameters({mv_->HIDDEN_DIM, mv_->HIDDEN_DIM})),
    // buffer lstm to parser state
    p_B(model.add_parameters({mv_->HIDDEN_DIM, mv_->HIDDEN_DIM})),
    // stack lstm to parser state
    p_S(model.add_parameters({mv_->HIDDEN_DIM, mv_->HIDDEN_DIM})),
    p_pbias(model.add_parameters({mv_->HIDDEN_DIM})),
    
    // predict the final action
    p_p2a(model.add_parameters({dict_map_->action_size(), mv_->HIDDEN_DIM})),
    p_abias(model.add_parameters({dict_map_->action_size()})),
    
    // reduce the tokens as phrase
    // head matrix for composition function
    p_H(model.add_parameters({mv_->LSTM_INPUT_DIM, mv_->LSTM_INPUT_DIM})),
    // dependency matrix for composition function
    p_D(model.add_parameters({mv_->LSTM_INPUT_DIM, mv_->LSTM_INPUT_DIM})),
    // relation matrix for composition function
    p_R(model.add_parameters({mv_->LSTM_INPUT_DIM, mv_->REL_DIM})),
    p_cbias(model.add_parameters({mv_->LSTM_INPUT_DIM}))
    {
        // if we are not using USE_POS, p_p will not exist
        if(mv_-> USE_POS)
        {
            p_p = model.add_lookup_parameters(dict_map_->pos_size(), {mv_->POS_DIM});
        }
        
        // Set up pretrained embedding
        // ??? if no pretrained embeddings(do nothing), p_t would be empty??
        // NOTE: THE pretrained embedding is lower cased here!
        // ??? so pretrained embeddings will only read existing words, and did not actually store OOVs??
        load_embedding(dict_map_->get_dict(DictMap::DICTMAP_IND_LC_TERM), mv_->pretrained_embedding_filepath, &p_t);
    }

    void init(Model& model)
    {
        if(mv_->USE_BROWN)
        {
            p_br4 = model.add_lookup_parameters(dict_map_->br4_size(), {mv_->POS_DIM});
            p_br6 = model.add_lookup_parameters(dict_map_->br6_size(), {mv_->POS_DIM});
            p_brall = model.add_lookup_parameters(dict_map_->brall_size(), {mv_->POS_DIM});
        }
    }
    
    Expression log_prob_parser(ComputationGraph& cg, Sentence& sent, bool build_training_graph, vector<unsigned int> &results)
    {
        //cout << sent.to_string() << endl;
        //cout << sent.size() << endl;
        unordered_map<string, Expression> named_expressions;
    
        // Initialize the parameters
        stack_lstm.new_graph(cg);
        buffer_lstm.new_graph(cg);
        action_lstm.new_graph(cg);
    
        // register "H", "D", "R" and "cbias" for later use in the state class
        // these will be to be assembled dynamically, stack element composition
        Expression H = parameter(cg, p_H);
        named_expressions["H"] = H;
        Expression D = parameter(cg, p_D);
        named_expressions["D"] = D;
        Expression R = parameter(cg, p_R);
        named_expressions["R"] = R;
        Expression cbias = parameter(cg, p_cbias);
        named_expressions["cbias"] = cbias;

        vector<Expression> input_words;

        // precompute buffer representation from left to right
        Expression word_start = parameter(cg, p_start_of_word);
        Expression word_end = parameter(cg, p_end_of_word);

        fw_char_lstm.new_graph(cg);
        bw_char_lstm.new_graph(cg);

        Expression x2ib = parameter(cg, p_x2ib);
        Expression x2i = parameter(cg, p_x2i);

        Expression root_in_char = parameter(cg, p_root_in_char);
    
        // prepare the buffer
        for (int i = 0; i < static_cast<int>(sent.size()); ++i)
        {
            //cout << "building word " << i << endl;
            vector<Expression> input_comps;
            Expression w_c_f; // the char level model of the word (forward), fw char word embeddings
            Expression w_c_b; // the char level model of the word (backward), bw char word embeddings
            Expression w; // the look up of the word

            if (dict_map_->is_root(sent.raw_terms[i]))
            {
                // Encoding for the root symbol.
                // if the word is ROOT
                w_c_f = root_in_char;
                w_c_b = root_in_char;
            }
            else
            {
                // Add the forward embedding
                fw_char_lstm.start_new_sequence();
                fw_char_lstm.add_input(word_start);
                // for word i
                for (int char_ind = 0; char_ind < static_cast<int>(sent.chars[i].size()); ++char_ind)
                {
                    Expression char_e = lookup(cg, p_c, sent.chars[i][char_ind]);
                    fw_char_lstm.add_input(char_e);
                }
                fw_char_lstm.add_input(word_end);

                // Add the backward embedding
                bw_char_lstm.start_new_sequence();
                bw_char_lstm.add_input(word_end);
                for (int char_ind = sent.chars[i].size() - 1; char_ind >= 0; --char_ind)
                {
                    Expression char_e = lookup(cg, p_c, sent.chars[i][char_ind]);
                    bw_char_lstm.add_input(char_e);
                }
                bw_char_lstm.add_input(word_start);

                // fw & bw char embedding output
                w_c_f = fw_char_lstm.back();
                w_c_b = bw_char_lstm.back();
            }
      
            // search for word embeddings of word i
            //w = lookup(cg, p_w, sent.terms[i]);

            input_comps.push_back(w_c_f);
            input_comps.push_back(w_c_b);
            //input_comps.push_back(w);

            Expression pos;
            if (mv_->USE_POS)
            {
                // pos embeddings
                pos = lookup(cg, p_p, sent.poss[i]);
            }
            else
            {
                pos = dynet::expr::zeroes(cg, {mv_->POS_DIM});
            }
            input_comps.push_back(pos);

            // Add brown clusters
            Expression br4, br6, brall; // look up of the brown clusters
            /*
            if(mv_->USE_BROWN)
            {
                br4 = lookup(cg, p_br4, sent.br_4[i]);
                br6 = lookup(cg, p_br6, sent.br_6[i]);
                brall = lookup(cg, p_brall, sent.br_all[i]);
            }
            else
            {
                br4 = dynet::expr::zeroes(cg, {mv_->POS_DIM});
                br6 = dynet::expr::zeroes(cg, {mv_->POS_DIM});
                brall = dynet::expr::zeroes(cg, {mv_->POS_DIM});
            }
            input_comps.push_back(br4);
            input_comps.push_back(br6);
            input_comps.push_back(brall);
             */

      
            // Add the pretrained embedding to the input representation
            Expression pretrain_emb = const_lookup(cg, p_t, sent.lower_cased_terms[i]);
            input_comps.push_back(pretrain_emb);

            Expression x = concatenate(input_comps);
            /*
             vector<float> x_value = as_vector(cg.get_value(x));
             assert(x_value.size() == 2 * mv_->LSTM_CHAR_OUTPUT_DIM + mv_->WORD_INPUT_DIM + mv_->POS_DIM + mv_->PRETRAINED_DIM);
            */
            //x = [p_fw, p_bw, p_w, p_p, p_t]
            //inputword = max{0, x2i * x + x2ib} final word embeddings
            Expression input_word = rectify(affine_transform({x2ib, x2i, x}));
            input_words.push_back(input_word);
        }

        assert(input_words.size() == sent.size());
    
        Expression stack_guard = parameter(cg, p_stack_guard);
        Expression buffer_guard = parameter(cg, p_buffer_guard);
        Expression action_guard = parameter(cg, p_action_guard);
    
        ParserState ps(&stack_lstm, &buffer_lstm, &action_lstm, &named_expressions, dict_map_, &sent);
        // Init the parser's state
        ps.init(stack_guard, buffer_guard, action_guard);
        //cout << "ps initialized." << endl;
        // Setup the buffer, get words into the buffer
        for (int ind = static_cast<int>((sent.size()-1)); ind >= 0; ind--)
        {
            //cout << "prepare word " << ind << endl;
            ps.buffer_push(input_words[ind], ind);
        }
        //cout << "buffer prepared." << endl;

        // Prepare the Expressions
        Expression S = parameter(cg, p_S);
        Expression B = parameter(cg, p_B);
        Expression A = parameter(cg, p_A);
        Expression p2a = parameter(cg, p_p2a);
        Expression abias = parameter(cg, p_abias);
        Expression pbias = parameter(cg, p_pbias);

        vector<Expression> log_probs;
        string rootword;
        unsigned action_count = 0;  // incremented at each prediction
        while(!ps.is_end_state())
        {
            // nl_cur_exp = max{0, A* out_A + B * out_B + S * out_S + p_pbias}
            Expression cur_exp = affine_transform({pbias, S, stack_lstm.back(), B, buffer_lstm.back(), A, action_lstm.back()});
      
            //vector<float> debug_exp_value = as_vector(cg.get_value(cur_exp));
            //assert(debug_exp_value.size() == mv_->HIDDEN_DIM);
            Expression nl_cur_exp = rectify(cur_exp);
            // adist = softmax(p2a * nl_cur_exp + abias)
            Expression r_t = affine_transform({abias, p2a, nl_cur_exp});
            Expression adiste = log_softmax(r_t);

            // Compute the scores for all the actions
            vector<float> adist = as_vector(cg.get_value(adiste));
      
            //for (auto debug_ele: adist) {
            //	cout << "DEBUG:" << debug_ele << endl;
            //}
            int predict_action = ps.next_action(adist);
            results.push_back(predict_action);

            if (build_training_graph)
            {
                if (sent.ref_actions[action_count] == predict_action)
                {
                    mv_->counter_correct_plus_one();
                }
                mv_->counter_total_plus_one();
            }
            int action = build_training_graph ? sent.ref_actions[action_count++] : predict_action;
            assert(adist.size() == dict_map_->action_size());
            //assert(action >= 0 && action < dict_map_->action_size());
            log_probs.push_back(pick(adiste, action));
      
            //float debug_value = as_scalar(cg.get_value(log_probs.back()));
            // cout << "DEBUG-VALUE: " << debug_value << endl;
            // Compute possible necessary embeddings
            // TODO: better ways to solve this via refactor
            Expression action_emb = lookup(cg, p_a, action);
            Expression relation_emb = lookup(cg, p_r, action);
            ps.perform_action(action, action_emb, relation_emb);
        }
        assert(log_probs.size() > 0);

        Expression tot_neglogprob = -sum(log_probs);
        //float debug_value_total = as_scalar(cg.get_value(tot_neglogprob));
        //cg.forward(tot_neglogprob);
        //cout << "DEBUG-VALUE-TOTAL: "<< debug_value_total << endl;
        return tot_neglogprob;
    }

    DictMap* get_dict_map()
    {
        return dict_map_;
    }

    //private:
public:
        ModelVars* mv_;
        DictMap* dict_map_;

        // parameters
        Parameter p_stack_guard;
        Parameter p_buffer_guard;
        Parameter p_action_guard;
        LSTMBuilder stack_lstm;
        LSTMBuilder buffer_lstm;
        LSTMBuilder action_lstm;

        Parameter p_start_of_word;
        Parameter p_end_of_word;
        LSTMBuilder fw_char_lstm;
        LSTMBuilder bw_char_lstm;

        LookupParameter p_w; // word embeddings
        Parameter p_root_in_char;
        LookupParameter p_c; // lookup for chars
        LookupParameter p_t; // pretrained word embeddings (not updated)
        Parameter p_x2i; // char, pos, word, pretrain to input
        Parameter p_x2ib; // bias for char, pos, word, pretrain to input
    
        // brown clusters
        LookupParameter p_br4;
        LookupParameter p_br6;
        LookupParameter p_brall;

        LookupParameter p_a; // input action embeddings
        LookupParameter p_r; // relation embeddings
        LookupParameter p_p; // pos tag embeddings
  
        Parameter p_A; // action lstm to parser state
        Parameter p_B; // buffer lstm to parser state
        Parameter p_S; // stack lstm to parser state
        Parameter p_pbias; // parser state bias
        Parameter p_p2a;   // parser state to action
        Parameter p_abias;  // action bias

        Parameter p_H; // head matrix for composition function
        Parameter p_D; // dependency matrix for composition function
        Parameter p_R; // relation matrix for composition function
        Parameter p_cbias; // composition function bias
};


namespace po = boost::program_options;

void InitCommandLine(int argc, char** argv, po::variables_map* conf)
{
    po::options_description opts("Configuration options");
    opts.add_options()
        ("training_data", po::value<string>(), "Training corpus")
        ("dev_data", po::value<string>(), "Development corpus")
        ("test_data", po::value<string>(), "Test corpus")
        ("files", po::value<vector<string>>()->multitoken(), "File names to be read")
        ("model", po::value<string>()->default_value(""), "Load saved model from this file")
        ("step_size", po::value<double>()->default_value(5e-4), "Step size for adam trainer")
        ("report_every_i", po::value<unsigned>()->default_value(1), "input embedding size")
        ("use_pos_tags", "make POS tags visible to parser")
        ("layers", po::value<unsigned>()->default_value(2), "number of LSTM layers")
        ("word_input_dim", po::value<unsigned>()->default_value(32), "input embedding size")
        ("char_input_dim", po::value<unsigned>()->default_value(10), "char input size")
        ("lstm_char_output_dim", po::value<unsigned>()->default_value(32), "the embedding size contributed from char-lstm")
        ("hidden_dim", po::value<unsigned>()->default_value(100), "hidden dimension")
        ("action_dim", po::value<unsigned>()->default_value(16), "action embedding size")
        ("pretrained_dim", po::value<unsigned>()->default_value(100), "pretrained input dimension")
        ("lstm_input_dim", po::value<unsigned>()->default_value(50), "the input dimension to LSTMs (stack, buffer, action)")
        ("pos_dim", po::value<unsigned>()->default_value(12), "POS dimension")
        ("rel_dim", po::value<unsigned>()->default_value(16), "relation dimension")
        ("pretrained_embedding_filepath", po::value<string>()->default_value(""), "Pretrained word embeddings")
        ("script_filepath", po::value<string>()->default_value(""), "eval script filepath")
        ("use_brown_clusters", "make brown clusters visible to parser")
        ("pretrained_model", po::value<string>()->default_value(""), "pretrained model to be loaded")
        ("save_model", "save model or not")
        ("fold", po::value<unsigned>(),"fold number")
        ("char_set_filepath", po::value<string>()->default_value(""), "char set filepath")
        ("pos_set_filepath", po::value<string>()->default_value(""), "pos set filepath")
        ("action_set_filepath", po::value<string>()->default_value(""), "action set filepath")
        ("help,h",  "Help");

    po::options_description dcmdline_options;
    dcmdline_options.add(opts);
    po::store(parse_command_line(argc, argv, dcmdline_options), *conf);
    if (conf->count("help"))
    {
        cerr << dcmdline_options << endl;
        exit(1);
    }
}

float eval_parses(string gold_file_path, string sys_file_path, string script_filepath)
{
    // Call Eval script
    string rm_temp_file = "rm -f " + script_filepath + "eval_results";
    const char* rm_cmd = rm_temp_file.c_str();
    system(rm_cmd);

    cerr << "running evaluation step." << endl;
    string eval_command = script_filepath + "tweet_calc_eval.sh " + gold_file_path + " " + sys_file_path + ">" + script_filepath + "eval_results";
    const char* eval_cmd = eval_command.c_str();~
    system(eval_cmd);

    std::ifstream infile(script_filepath + "eval_results");
    assert(infile);
    std::string line;

    float score = 0;

    while (std::getline(infile, line))
    {
        boost::algorithm::trim(line);
        if (line.length() == 0) continue;
        score = std::stof(line);
        break;
    }
    return score;
}

void predict(ParserBuilder& parser_builder, vector<Sentence> corpus, string output)
{
    ofstream o(output);
    for (int i = 0; i < static_cast<int>(corpus.size()); ++i)
    {
        ComputationGraph cg;
        auto& sent = corpus[i];
        vector<unsigned int> results;
        parser_builder.log_prob_parser(cg, sent, false, results);
        for (int j = 0; j < static_cast<int>(sent.size()); j++)
        {
            string word = sent.raw_terms[j];
            string pos = ((parser_builder.get_dict_map())->get_dict(DictMap::DICTMAP_IND_POS)).convert(sent.poss[j]);
            string wp = word + '/' + pos;
            o << wp;
            if (j == static_cast<int>(sent.size() - 1))
            {
                o << " ||| ";
            }
            else
            {
                o << " ";
            }
        }
        for (int j = 0; j < static_cast<int>(results.size()); ++j)
        {
            string action = ((parser_builder.get_dict_map())->get_dict(DictMap::DICTMAP_IND_ACTION)).convert(results[j]);
            o << action;
            if (j == static_cast<int>(results.size() - 1))
            {
                o << "\n";
            }
            else
            {
                o << " ";
            }
        }
    }
    o.close();
}


int main(int argc, char** argv)
{
    dynet::initialize(argc, argv);

    po::variables_map conf;
    InitCommandLine(argc, argv, &conf);

    // Initialize the contextLSTM_INPUT_DIM}
    DictMap dict_map;
    ModelVars mv;

    mv.LAYERS = conf["layers"].as<unsigned>();
    mv.WORD_INPUT_DIM = conf["word_input_dim"].as<unsigned>();
    mv.CHAR_INPUT_DIM = conf["char_input_dim"].as<unsigned>();
    mv.LSTM_CHAR_OUTPUT_DIM = conf["lstm_char_output_dim"].as<unsigned>();
    mv.HIDDEN_DIM = conf["hidden_dim"].as<unsigned>();
    mv.ACTION_DIM = conf["action_dim"].as<unsigned>();
    mv.PRETRAINED_DIM = conf["pretrained_dim"].as<unsigned>();
    mv.LSTM_INPUT_DIM = conf["lstm_input_dim"].as<unsigned>();
    mv.POS_DIM = conf["pos_dim"].as<unsigned>();
    mv.REL_DIM = conf["rel_dim"].as<unsigned>();
    mv.pretrained_embedding_filepath = conf["pretrained_embedding_filepath"].as<string>();
    mv.model_filepath = conf["model"].as<string>();
    mv.USE_POS = conf.count("use_pos_tags");
    mv.USE_BROWN = conf.count("use_brown_clusters");
    mv.pretrained_model = conf["pretrained_model"].as<string>();
    mv.SAVE_MODEL = conf.count("save_model");
    int cross = conf.count("fold");
    mv.char_set_filepath = conf["char_set_filepath"].as<string>();
    mv.pos_set_filepath = conf["pos_set_filepath"].as<string>();
    mv.action_set_filepath = conf["action_set_filepath"].as<string>();

    
    int it, best_iteration;
    int idx;
    if(cross)
    {
        //cross
        best_iteration = it = 0;
        idx = conf["fold"].as<unsigned>();
    }

    // Log the model hyper parameters.
    cerr << mv.to_string() << endl;
    cerr << "FOLD COUNT: " << cross << endl;
    cerr << "Eval Script Filepath: " << conf["script_filepath"].as<string>() <<endl;
    
    load_char_set(mv.char_set_filepath, dict_map);
    cerr << "Char Set: " << dict_map.char_size() << endl;
    load_pos_set(mv.pos_set_filepath, dict_map);
    cerr << "POS Set: " << dict_map.pos_size() << endl;
    load_action_set(mv.action_set_filepath, dict_map);
    cerr << "Action Set: " << dict_map.action_size() << endl;
    
    vector<Sentence> corpus_train = read_from_file(conf["training_data"].as<string>(), dict_map, false),
    corpus_dev = read_from_file(conf["dev_data"].as<string>(), dict_map, false),
    corpus_test = read_from_file(conf["test_data"].as<string>(), dict_map, false);
    
    dict_map.freeze();
    cerr << "Training: " << corpus_train.size() << " sentences from " << conf["training_data"].as<string>() << endl;
    cerr << "Dev: " << corpus_dev.size() << " sentences from " << conf["dev_data"].as<string>() << endl;
    cerr << "Test: " << corpus_test.size() << " sentences from " << conf["test_data"].as<string>() << endl;
    
    // Log the dict map status
    //cerr << dict_map.to_string() << endl;
    Model model, nonsave_model;
    ParserBuilder parser_builder(model, nonsave_model, &mv, &dict_map);
    
    for(auto& para: model.lookup_parameters_list())
    {
        cerr << para->all_dim << endl;
    }
    cerr << "#Look up Parameter: " << model.lookup_parameters_list().size() << endl;
    for(auto& para: model.parameters_list())
    {
        cerr << para->dim << endl;
    }
    cerr << "#Parameter: " << model.parameters_list().size() << endl;
    
    //parser_builder.init(model);
    if(mv.pretrained_model != "")
    {
        dynet::load_dynet_model(mv.pretrained_model, &model);
    }
    
    for(auto& para: model.lookup_parameters_list())
    {
        cerr << para->all_dim << endl;
    }
    cerr << "#Look up Parameter after loading model: " << model.lookup_parameters_list().size() << endl;
    for(auto& para: model.parameters_list())
    {
        cerr << para->dim << endl;
    }
    cerr << "#Parameter after loading model: " << model.parameters_list().size() << endl;
    
    //auto sgd = new AdamTrainer(&model, 1e-6, conf["step_size"].as<double>(), 0.01, 0.9999, 1e-8);
    //auto sgd = new AdamTrainer(&model, 1e-6, 0.01, 0.9999, 1e-8);

    auto sgd = new MomentumSGDTrainer(model, 0.01, 0.9, 0.1);
  
    //training corpus sentence number
    unsigned si = 0;
    vector<unsigned> order(corpus_train.size());
    for (int i = 0; i < static_cast<int>(order.size()); ++i)
    {
        order[i] = i;
    }
    
    int report = 0;
    int epoch_num = 0;
    const int EPOCH_LIMIT = 100;

    float current_best_dev = 0.0;
    float current_best_test = 0.0;
    
    while(1)
    {
        Timer iteration("completed in");
        double loss = 0.0;
        //epoch
        for (int i = 0; i < 100; ++i)
        {
            if (si == corpus_train.size())
            {
                si = 0;
                sgd->update_epoch();
                epoch_num ++;
                if(mv.SAVE_MODEL)
                {
                    string filename = "model_epoch_" + boost::lexical_cast<string>(epoch_num);
                    dynet::save_dynet_model(filename, &model);
                }
                if(epoch_num == EPOCH_LIMIT)
                {
                    return 0;
                }
                //cerr << "**SHUFFLE\n";
                shuffle(order.begin(), order.end(), *rndeng);
            }
            // construct graph
            ComputationGraph cg;
            auto& sent = corpus_train[order[si]];
            ++si;
            vector<unsigned int> results;
            Expression loss_expr = parser_builder.log_prob_parser(cg, sent, true, results);
            loss += as_scalar(cg.forward(loss_expr));
            cg.backward(loss_expr);
            sgd->update(1.0);
        }
        sgd->status();
        cerr << "acc = " << mv.current_acc() << endl;
        mv.counter_clean();
        report++;
        if (report % (conf["report_every_i"].as<unsigned>()) == 0)
        {
            it ++;
            // Begin the training loop
            string dev_output = mv.model_filepath + ".dev.pred";
            string test_output = mv.model_filepath + ".test.pred";
            cerr << "DEBUG Path:"<<dev_output <<endl;
            // For simplicity, we just reuse the parser builder here, but it should be totally okay when you
            // save mv, model and dictmap and rebuild the parser builder
            predict(parser_builder, corpus_dev, dev_output);
            float dev_score = eval_parses(conf["dev_data"].as<string>(), dev_output, conf["script_filepath"].as<string>());
            cerr << "score dev: " << dev_score << endl;
            predict(parser_builder, corpus_test, test_output);
            float test_score = eval_parses(conf["test_data"].as<string>(), test_output, conf["script_filepath"].as<string>());
            cerr << "score test: " << test_score  << endl;
            // only compare dev score
            if (dev_score > current_best_dev)
            {
                current_best_dev = dev_score;
                current_best_test = test_score;
                //cross
                best_iteration = it;
            }
            cerr << "current best dev: " << current_best_dev << " current best test: " << current_best_test << endl;
            //cross
            cout << "best iteration: " << best_iteration << " in fold " << idx << endl;
            
            if(it == 35)
            {
                string filename = "model_final";
                dynet::save_dynet_model(filename, &model);
                return 0;
            } 
        }
    }
}
