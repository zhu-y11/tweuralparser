#ifndef NTPARSER_DICTMAP_HPP_
#define NTPARSER_DICTMAP_HPP_

#include <unordered_map>
#include "dynet/dict.h"
#include <string>

class DictMap
{
    public:
        // These are indices
        // word dictionary
        static const int DICTMAP_IND_TERM = 0;
        // lower cased dictionary
        static const int DICTMAP_IND_LC_TERM = 1;
        // pos dictionary
        static const int DICTMAP_IND_POS = 2;
        // character dictionary
        static const int DICTMAP_IND_CHARCTER = 3;
        // action dictionary
        static const int DICTMAP_IND_ACTION = 4;
        // BR 4 dictionary
        static const int DICTMAP_IND_BR4 = 5;
        // BR 6 dictionary
        static const int DICTMAP_IND_BR6 = 6;
        // BR all dictionary
        static const int DICTMAP_IND_BRALL = 7;

        // How many dict we have
        static const int DICTMAP_INDSIZE = 8;
  
        DictMap()
        {
            for(int i = 0; i < DICTMAP_INDSIZE; i++)
            {
                // Not create anything, but make sure all the dict are there
                get_dict(i);
            }
        };

    ~DictMap(){};
  
    // Freeze all the dictionaries
    void freeze()
    {
        for(int i = 0; i < DICTMAP_INDSIZE; i++)
        {
            get_dict(i).freeze();
            get_dict(i).set_unk("<UNK>");
        }
    }

    dynet::Dict& get_dict(int mapcom)
    {
        return dict_map[mapcom];
    }

    unsigned vocab_size()
    {
        return dict_map.at(DICTMAP_IND_TERM).size();
    }

    unsigned lc_vocab_size()
    {
        return dict_map.at(DICTMAP_IND_LC_TERM).size();
    }

    unsigned pos_size()
    {
        return dict_map.at(DICTMAP_IND_POS).size();
    }

    unsigned action_size()
    {
        return dict_map.at(DICTMAP_IND_ACTION).size();
    }

    unsigned char_size()
    {
        return dict_map.at(DICTMAP_IND_CHARCTER).size();
    }
    
    unsigned br4_size()
    {
        return dict_map.at(DICTMAP_IND_BR4).size();
    }
    
    unsigned br6_size()
    {
        return dict_map.at(DICTMAP_IND_BR6).size();
    }
    
    unsigned brall_size()
    {
        return dict_map.at(DICTMAP_IND_BRALL).size();
    }

    void set_root(std::string rs)
    {
        root_string = rs;
    }

    bool is_root(std::string rs)
    {
        return (root_string.compare(root_string) == 0);
    }

    private:
        std::unordered_map<int, dynet::Dict> dict_map;
        std::string root_string = "<ROOT>";
};

const int DictMap::DICTMAP_IND_TERM;
const int DictMap::DICTMAP_IND_LC_TERM;
const int DictMap::DICTMAP_IND_POS;
const int DictMap::DICTMAP_IND_CHARCTER;
const int DictMap::DICTMAP_IND_ACTION;
const int DictMap::DICTMAP_IND_BR4;
const int DictMap::DICTMAP_IND_BR6;
const int DictMap::DICTMAP_IND_BRALL;
const int DictMap::DICTMAP_INDSIZE;

#endif
