#ifndef NTPARSER_CONLL_READER_HPP_
#define NTPARSER_CONLL_READER_HPP_

#include <unordered_map>
#include <fstream>
#include <boost/algorithm/string.hpp>
#include "dict_map.hpp"
#include "dynet/dynet.h"
#include "dynet/model.h"

struct Sentence
{
    std::vector<std::string> raw_terms;
    std::vector<int> terms;

    std::vector<std::string> raw_lower_cased_terms;
    std::vector<int> lower_cased_terms;

    std::vector<int> poss;
    std::vector<std::vector<int>> chars;
    
    std::vector<int> br_4;
    std::vector<int>br_6;
    std::vector<int>br_all;

    // TODO: ADD REFERENCE ACTIONS
    std::vector<int> ref_actions;

    unsigned size()
    {
        return raw_terms.size();
    }

    std::string to_string()
    {
        std::string joined = boost::algorithm::join(raw_terms, " ");
        joined = joined + "\n";
        for (unsigned i = 0; i < terms.size(); ++i)
        {
            joined = joined + std::to_string(terms[i]) + " ";
        }
        return joined;
    }
};

void load_embedding(dynet::Dict& d, std::string pretrain_path, dynet::LookupParameter* p_labels)
{
    std::ifstream fin(pretrain_path);
    std::string s;
    // word d1 d2 d3 ... dn (n dimensions)
    while(getline(fin,s))
    {
        std::vector <std::string> fields;
        boost::algorithm::trim(s);
        boost::algorithm::split(fields, s, boost::algorithm::is_any_of( " " ));
        std::string word = fields[0];
        std::vector<float> p_embeding;
        for(unsigned ind = 1; ind < fields.size(); ++ind)
        {
            p_embeding.push_back(std::stod(fields[ind]));
        }
        if(d.contains(word))
        {
            // cout << "init" << endl;
            p_labels->initialize(d.convert(word), p_embeding);
        }
    }
}

// given the first character of a UTF8 block, find out how wide it is
// see http://en.wikipedia.org/wiki/UTF-8 for more info
inline unsigned int UTF8Len(unsigned char x)
{
    if (x < 0x80) return 1;
    else if ((x >> 5) == 0x06) return 2;
    else if ((x >> 4) == 0x0e) return 3;
    else if ((x >> 3) == 0x1e) return 4;
    else if ((x >> 2) == 0x3e) return 5;
    else if ((x >> 1) == 0x7e) return 6;
    else abort();
}

// TODO: READ NECESSARY THINGS HERE
Sentence parse_input_line(std::string line, DictMap& dict_map, bool use_brown)
{
    std::istringstream in(line);
    std::string sep = "|||";
    std::string temp;
  
    Sentence sent;

    /* 
        the input looks like:
        <ROOT>/<ROOT> word1/pos1 word2/pos2 word3/pos3 word4/pos4 word5/pos5 ||| action1 action2/label action3/label action4
    */
    // get the part before |||
    while(1)
    {
        // word/poss
        in >> temp;
        if (temp == sep) break;
        std::string word, pos, br4, br6, brall;
        if(use_brown)
        {
            std::vector <std::string> fields(5);
            for(int i = 4; i >= 1; i--)
            {
                size_t p = temp.rfind('/');
                //std::cout << temp << std::endl;
                if (p == std::string::npos || p == 0 || p == (word.size()-1))
                {
                    std::cerr << "mal-formed POS tags: " << temp << std::endl;
                    std::cerr << p << std::endl;
                    abort();
                }
                fields[i] = temp.substr(p + 1);
                temp = temp.substr(0, p);
                if(i == 1)
                {
                    fields[0] = temp;
                }
            }
            word = fields[0];
            pos = fields[1];
            br4 = fields[2];
            br6 = fields[3];
            brall = fields[4];
            sent.br_4.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_BR4).convert(br4));
            sent.br_6.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_BR6).convert(br6));
            sent.br_all.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_BRALL).convert(brall));
        }
        else
        {
            size_t p = temp.rfind('/');
            if (p == std::string::npos || p == 0 || p == (word.size()-1))
            {
                std::cerr << "mal-formed POS tags: " << temp << std::endl;
                std::cerr << p << std::endl;
                abort();
            }
            word = temp.substr(0, p);
            pos = temp.substr(p+1);
            //std::cout << word << ' ' << pos << std::endl;
        }
        sent.raw_terms.push_back(word);
        sent.terms.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_TERM).convert(word));
        sent.poss.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_POS).convert(pos));

        // break the word into characters and prepare the character settings
        size_t cur = 0;
        std::vector<int> word_chars;
        while(cur < word.size())
        {
            size_t len = UTF8Len(word[cur]);
            word_chars.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_CHARCTER).convert(word.substr(cur,len)));
            cur += len;
        }
        sent.chars.push_back(word_chars);

        // lowercase the word
        std::string word_lc(word);
        boost::algorithm::to_lower(word_lc);
        sent.raw_lower_cased_terms.push_back(word_lc);
        sent.lower_cased_terms.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_LC_TERM).convert(word_lc));
    }

    // get the part after |||
    while(1)
    {
        // read the labels
        in >> temp;
        if (!in) break;
        std::string action(temp);
        // gold standard
        // action1 action2/label
        sent.ref_actions.push_back(dict_map.get_dict(DictMap::DICTMAP_IND_ACTION).convert(action));
    }
    return sent;
}


std::vector<Sentence> read_from_file(std::string file_path, DictMap& dict_map, bool use_brown = false)
{
    std::ifstream infile(file_path);
    assert(infile);
    std::vector<Sentence> corpus;
    std::string line;
    while (std::getline(infile, line))
    {
        boost::algorithm::trim(line);
        if (line.length() == 0)
        {
            break;
        }
        Sentence s = parse_input_line(line, dict_map, use_brown);
        corpus.push_back(s);
    }
    return corpus;
}


void load_char_set(std::string char_set_filepath, DictMap& dict_map)
{
    std::ifstream infile(char_set_filepath);
    assert(infile);
    std::string line;
    while(std::getline(infile, line))
    {
        boost::algorithm::trim(line);
        if (line.length() == 0)
        {
            break;
        }
        dict_map.get_dict(DictMap::DICTMAP_IND_CHARCTER).convert(line);
    }
    dict_map.get_dict(DictMap::DICTMAP_IND_CHARCTER).freeze();
    dict_map.get_dict(DictMap::DICTMAP_IND_CHARCTER).set_unk("<UNK>");
}


void load_pos_set(std::string pos_set_filepath, DictMap& dict_map)
{
    std::ifstream infile(pos_set_filepath);
    assert(infile);
    std::string line;
    while(std::getline(infile, line))
    {
        boost::algorithm::trim(line);
        if (line.length() == 0)
        {
            break;
        }
        dict_map.get_dict(DictMap::DICTMAP_IND_POS).convert(line);
    }
    dict_map.get_dict(DictMap::DICTMAP_IND_POS).freeze();
}

void load_action_set(std::string action_set_filepath, DictMap& dict_map)
{
    std::ifstream infile(action_set_filepath);
    assert(infile);
    std::string line;
    while(std::getline(infile, line))
    {
        boost::algorithm::trim(line);
        if (line.length() == 0)
        {
            break;
        }
        dict_map.get_dict(DictMap::DICTMAP_IND_ACTION).convert(line);
    }
    dict_map.get_dict(DictMap::DICTMAP_IND_ACTION).freeze();
}

#endif
