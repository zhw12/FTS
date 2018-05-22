
# coding: utf-8

# In[2]:


'''
__author__ : Hanwen Zha
__description__: Function for attach a node to the general taxonomy
__latest_update__: 2/27/2018
'''


from gensim.models import word2vec
from collections import Counter
# from tqdm import tqdm_notebook
import re
from pprint import pprint
import os


# In[5]:


from .util import ES
from .util import rmTag_concat
from .util import wrapTag
from .util import rmUnderscore
from .util import cleanText


import sys
import spacy
import json
from tqdm import tqdm
# import ipdb
from spacy.tokens import Doc
from spacy.matcher import PhraseMatcher

try:
  unicode;
except NameError as e:
  unicode = str

class WhitespaceTokenizer(object):
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split(' ')
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)

nlp = spacy.load('en', disable=['ner', 'parser', 'tagger'])
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)

# In[6]:

root_dir = os.path.abspath('.') # /home/hanwen/disk/demov3
# print('. is', os.path.abspath('.'), 'in attach_taxonomy')
# root_dir = '/home/hanwen/disk/demov3'


# load word embedding
# file_word2vec = '{}/concept_based_retrieval/output/SEMANTIC_SCHOLAR120w/wordvec'.format(root_dir)
# model = word2vec.Word2Vec.load(file_word2vec)


# load taxonomy
with open('{}/data/generated_taxonomy/tree.json'.format(root_dir)) as f_in:
    taxonomy_data = json.load(f_in)
with open('{}/webUI/attach_taxonomy/total_dict.json'.format(root_dir)) as fin:
    total_dict = json.load(fin)
with open('{}/webUI/attach_taxonomy/total_dict_loose.json'.format(root_dir)) as fin:
    total_dict_loose = json.load(fin)

class taxonomy_tree():
    def __init__(self):
        self.tree_list = []
    def parse_tree(self, node, level):
        if level == 0:
            self.tree_list.append({'name':node['name'], 'keywords':node['keywords'], 'level':level})
        if 'children' not in node:
            self.tree_list.append({'name':node['name'], 'keywords':node['keywords'], 'level':level})
            return
        if 'children' in node:
            self.tree_list.append({'name':node['name'], 'keywords':node['keywords'], 'level':level})
            for child in node['children']:
                n = self.parse_tree(child, level+1)
    def output_tree_by_level(self):
        output_tree_list = []
        for lvl in range(4):
            for node in self.tree_list:
                if node['level'] == lvl:
                    output_tree_list.append(node)
        return output_tree_list


def flatten(matched_phrase_docs):
    flat_matched_phrase_docs = []
    for matched_phrase_doc in matched_phrase_docs:
        for doc in matched_phrase_doc:
            flat_matched_phrase_docs.append(doc)
    return flat_matched_phrase_docs

def flatten_once(matched_phrase_docs):
    flat_matched_phrase_docs = []
    for matched_phrase_doc in matched_phrase_docs:
        for doc in set(matched_phrase_doc):
            flat_matched_phrase_docs.append(doc)
    return flat_matched_phrase_docs


def attach_taxonomy(query, model):
    #  e.g. query = 'quantum_learning'
    tree = taxonomy_tree()
    tree.parse_tree(taxonomy_data, 0)
    tree_list = tree.output_tree_by_level()


    general_taxonomy_phrases = []
    general_taxonomy_keywords = []
    for node in tree_list:
        general_taxonomy_phrases.append(node['name'])
        general_taxonomy_keywords.extend(node['keywords'])


    general_taxonomy_phrases.remove('quantum')


    general_taxonomy_phrases = [rmUnderscore(node) for node in general_taxonomy_phrases]
    general_taxonomy_keywords = [rmUnderscore(node) for node in general_taxonomy_keywords] 


    INDEX_NAME = "taxongen1"
    TYPE_NAME = "taxongen_docs"
    es = ES(index_name=INDEX_NAME, type_name=TYPE_NAME)


    isprint = False

    ids, total = es.search_articles_by_phrase(query.replace('_', ' '))
    ids_loose, total_loose = es.search_articles_by_common_term(query.replace('_', ' '))

    texts = es.search_articles_by_ids(ids)
    texts = [cleanText(line) for line in texts]

    texts_loose = es.search_articles_by_ids(ids_loose)
    texts_loose = [cleanText(line) for line in texts_loose]

    sim_list = []
    for node in tree_list:
        if node['level'] >= 4:
            continue
        try:
            sim = model.wv.similarity(wrapTag(node['name']), wrapTag(query))
            sim_list.append([node['name'], sim])
        except KeyError as e:
            sim_list.append([node['name'], 0])

    if isprint:
        print('\n')
        print('sim_list -->')
        pprint(sim_list[:10])

    sorted_sim_list = sorted(sim_list, key=lambda x:-x[1])
    if isprint:
        print('\n')
        print('sorted_sim_list -->')
        pprint(sorted_sim_list[:10])

    # these phrases are limited
    phrases = general_taxonomy_phrases

    # build phrase matcher
    matcher = PhraseMatcher(nlp.vocab)
    for v in phrases:
        matcher.add(v, None, nlp(unicode(v))) # python3 is unicode

    # matcher.add(v, None, nlp(unicode(query.replace('_', ' '))))

    phrase_docs = []
    # for text in tqdm_notebook(texts):
    for text in texts:
        doc = nlp(text.lower())
        matches = matcher(doc)
        nps = []
        prev_st = 0
        prev_ed = 0
        for m in matches:
            tokens = text.lower().split(' ')
            st = m[1]
            ed = m[2]
            if ed > prev_ed:
                np = {'st':st, 'ed':ed, 'text': '_'.join(tokens[st:ed])}
                nps.append(np)
                prev_ed = ed
        phrase_docs.append([np['text'] for np in nps])

    phrase_docs_loose = []
    # for text in tqdm_notebook(texts_loose):
    for text in texts_loose:
        doc = nlp(text.lower())
        matches = matcher(doc)
        nps = []
        prev_st = 0
        prev_ed = 0
        for m in matches:
            tokens = text.lower().split(' ')
            st = m[1]
            ed = m[2]
            if ed > prev_ed:
                np = {'st':st, 'ed':ed, 'text': '_'.join(tokens[st:ed])}
                nps.append(np)
                prev_ed = ed
        phrase_docs_loose.append([np['text'] for np in nps])

    flat_matched_phrase_docs = flatten(phrase_docs)
    flat_matched_phrase_docs_loose = flatten(phrase_docs_loose)

    coocur_cnter = Counter(flat_matched_phrase_docs)
    coocur_cnter_loose = Counter(flat_matched_phrase_docs_loose)

    # -------------------
    flat_matched_phrase_docs = flatten_once(phrase_docs)
    flat_matched_phrase_docs_loose = flatten_once(phrase_docs_loose)
    coocur_cnter_once = Counter(flat_matched_phrase_docs)
    coocur_cnter_loose_once = Counter(flat_matched_phrase_docs_loose)

    if isprint:
        print('\n')
        print('coocur_cnter -->')
        pprint(coocur_cnter.most_common(20))

        print('\n')
        print('coocur_cnter_loose -->')
        
        pprint(coocur_cnter_loose.most_common(20))


        
        print('\n')
        print('coocur_cnter -->')
        pprint(coocur_cnter_once.most_common(20))

        print('\n')
        print('coocur_cnter_loose -->')
        
        pprint(coocur_cnter_loose_once.most_common(20))



    if total < 500:
        use_dict = total_dict_loose
        use_total = total_loose
        use_coour_counter_once = coocur_cnter_loose_once
    else:
        use_dict = total_dict
        use_total = total
        use_coour_counter_once = coocur_cnter_once
        
    norm = sum([p[1] for p in use_coour_counter_once.most_common(10)])

    # ratio_threshold = 0.05
    hard_threshold = 5
    
    top_phrases = {}
    for idx, p in enumerate(use_coour_counter_once.most_common(10)):
        phrase, freq = p
    #     flag = 0
    #     freq/min(use_dict.get(phrase, 100000), use_total, 10000) >= ratio_threshold and
        if freq < hard_threshold:  
            continue
        try:
            embeding_sim = model.similarity(wrapTag(phrase), wrapTag(query))
        except:
            embeding_sim = None
        if embeding_sim and embeding_sim < 0.3:
            continue
            
        # print(phrase, freq, use_total, use_dict[phrase], end=' ')
        # print(round(embeding_sim, 2), end = ' ')
        # print(round(freq/norm, 2)) 
        
        if round(freq/norm, 2) > .1 or idx < 3:
            top_phrases[phrase] = round(freq/norm, 2)
    return top_phrases


# top_phrases = attach_taxonomy(query='machine_learning', model=model)
# print(top_phrases)