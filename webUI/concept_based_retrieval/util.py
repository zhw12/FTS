import re
import time
from functools import wraps

# import networkx as nx
import numpy as np
from gensim import corpora, models, similarities
from gensim.models import word2vec


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print ('Elapsed time: {}'.format(end - start))
        return result
    return wrapper


MIN_NEIGHBOR_SIMILARITY = .6
MIN_CATEGORY_NEIGHBOR = 3
MAX_NEIGHBORS = 100
THRESHOLD = .99


# file_wordvec = sys.argv[1]
# file_wordvec = '/home/hanwen/Desktop/demo/NSCTA-Demo/concept_based_retrieval/output/SEMANTIC_SCHOLAR/wordvec'
file_wordvec = 'embedding/word2vec_fixed_pretrained.bin'
# file_wordvec = 'embedding/wordvec'

def reverseDict(dict):
    return {v: k for k, v in dict.items()}


model_concepts = word2vec.Word2Vec.load(file_wordvec)
# G = nx.Graph()

ind2label_concepts = model_concepts.wv.index2word
label2ind_concepts = reverseDict(
    {k: v for k, v in enumerate(ind2label_concepts)})


abnormal_phrase = re.compile(
    r".*[-_]{2,}.*$"
)

def searchConcept(query):
    return [w for w in ind2label_concepts if query in w and not abnormal_phrase.match(w)]


def displayString(w):
    return re.sub(r'</?phrase>', '', w).replace('_', ' ').replace('-', ' ')

# def displayString(w):
#     return re.sub(r'</?phrase>', '', w).replace('_', ' ')


def wrap_marker(w):
    return '<phrase>%s</phrase>' % w.replace(' ', '_')


def is_phrase(w):
    return w.startswith('<phrase>') and w.endswith('</phrase>')


def get_res(name):
    if not name:
        return
    # allow user to input space separted words
    name = '_'.join(filter(bool, name.split(' ')))
    # return '\n'.join([displayString(c) for c in searchConcept(name)])
    return [displayString(c) for c in searchConcept(name)]


print('helper loaded..')


def flatten(list):
    return [item for sublist in list for item in sublist]


# def getConceptIDs(seed_concepts, label2ind_concepts):
#     def lookup(w, label2ind_concepts):
#         result = label2ind_concepts.get('<phrase>%s</phrase>' % w.lower())
#         if result is not None:
#             return result
#         result = label2ind_concepts.get(w)
#         if result is not None:
#             return result
#     l = [lookup(w.lower(), label2ind_concepts) for w in seed_concepts]
#     return [d for d in l if d is not None]
#
#
# @timing
# def get_concept_label_PPR():
#     # import ipdb; ipdb.set_trace()
#     # model_concepts = word2vec.Word2Vec.load(file_wordvec)
#
#     ind2label_concepts = model_concepts.wv.index2word
#     label2ind_concepts = reverseDict(
#         {k: v for k, v in enumerate(ind2label_concepts)})
#
#     # ind2label_concepts = [w for w in ind2label_concepts if '_' in w or w in seed_concepts_set]
#     ind2label_concepts = [w for w in ind2label_concepts if '_' in w]
#     label2ind_concepts = reverseDict(
#         {k: v for k, v in enumerate(ind2label_concepts)})
#
#     # G = nx.Graph()
#     for w in ind2label_concepts:
#         G.add_node(w, label=w, id=w)
#     for w in ind2label_concepts:
#         neighbor_wWeights = [
#             (word, score) for word, score in model_concepts.most_similar(w, topn=MAX_NEIGHBORS)]
#         # MIN_CATEGORY_NEIGHBOR
#         num_neighbors = 0
#         for neighbor, weight in neighbor_wWeights:
#             if weight < MIN_NEIGHBOR_SIMILARITY:
#                 # if w in seed_concept_set and num_neighbors < MIN_CATEGORY_NEIGHBOR:
#                 if num_neighbors < MIN_CATEGORY_NEIGHBOR:
#                     # print w
#                     pass
#                 else:
#                     break
#
#             G.add_edge(w, neighbor, weight=weight)
#             num_neighbors += 1
#
#
# def query_PPR(seed_concepts_list):
#     category_name_list = []
#     category_name_list.append('cs.ML')
#     seed_conceptsAsIds = [getConceptIDs(
#         seed_concepts, label2ind_concepts) for seed_concepts in seed_concepts_list]
#     seed_concepts_set = set([ind2label_concepts[i]
#                              for i in flatten(seed_conceptsAsIds)])
#
#     seed_conceptsAsIds = [getConceptIDs(
#         seed_concepts, label2ind_concepts) for seed_concepts in seed_concepts_list]
#     seed_concept_sets = [set([ind2label_concepts[i] for i in seed_conceptsAsId])
#                          for seed_conceptsAsId in seed_conceptsAsIds]
#     seed_concept_set = set(flatten(seed_concept_sets))
#
#     for ind in seed_concepts_set:
#         print(ind, 'similar neighbors:', model_concepts.most_similar(ind, topn=10))
#
#     for x in seed_concept_sets:
#         print(x)
#     print('before ppr...')
#     pprs = []
#     for category in range(len(seed_conceptsAsIds)):
#         personalization_weight = {
#             w: 1 if w in seed_concept_sets[category] else 0 for w in ind2label_concepts}
#         pprs.append(nx.pagerank(G, personalization=personalization_weight))
#         print('finished category %s' % category_name_list[category])
#     # import ipdb; ipdb.set_trace()
#     # print(pprs)
#     return pprs
#
#
# @timing
# def query_s(query, topn=10):
#     seed_concepts_list = []
#     seed_concepts_list.append([query])
#     pprs = query_PPR(seed_concepts_list)
#     ppr1 = pprs[0]
#     return sorted(ppr1, key=lambda p: ppr1[p], reverse=True)[:]

# get_concept_label_PPR()
# query_s('deep_learning')
