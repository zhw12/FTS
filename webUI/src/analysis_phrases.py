import json
import re
import string
import time

from elasticsearch import Elasticsearch
from gensim.models import word2vec


def displayString(w):
    return re.sub(r'</?phrase>', '', w).replace('_', ' ').replace('-', ' ')


def wrap_marker(w):
    return '<phrase>%s</phrase>' % w.replace(' ', '_')


def is_phrase(w):
    return w.startswith('<phrase>') and w.endswith('</phrase>')

class ES():
    def __init__(self, index_name, type_name, model_concepts, request_timeout=180):
        self.INDEX_NAME = index_name
        self.TYPE_NAME = type_name
        self.REQUEST_TIMEOUT = request_timeout
        self.TITLE_WIEGHT = 16
        self.BODY_WEIGHT = 3
        self.es = Elasticsearch()
        self.model_concepts = model_concepts

    def search_articles_by_phrase(self, phrase, id_only=True):
        # if phrase in self.model_concepts:
        #     pass
        # else:
        #     phrase = wrap_marker(phrase)
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            'common': {
                                'title': {
                                    'query': phrase,
                                    'cutoff_frequency': 0.001,
                                }
                            },
                        },
                        {
                            'common': {
                                'paperAbstract': {
                                    'query': phrase,
                                    'cutoff_frequency': 0.001,
                                }
                            },
                        },
                        # {"match_phrase": {"title": {"query": phrase, "boost": self.TITLE_WIEGHT}}},
                        # {"match_phrase": {"article": {"query": phrase, "boost": self.BODY_WEIGHT}}}
                    ]
                }
            }
        }
        if id_only:
            search_body["_source"] = ["sid"]

        res = self.es.search(index=INDEX_NAME, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
        print("Phrase: %s, Total hits = %s" % (phrase, res['hits']['total']))
        # id_list = [(hit["_source"]["sid"]) for hit in res["hits"]["hits"]]
        return res['hits']['total']


if __name__ == "__main__":
    INDEX_NAME = "taxongen1"
    TYPE_NAME = "taxongen_docs"
    file_wordvec = 'concept_based_retrieval/output/SEMANTIC_SCHOLAR120w/wordvec'
    model_concepts = word2vec.Word2Vec.load(file_wordvec)
    es = ES(index_name=INDEX_NAME, type_name=TYPE_NAME, model_concepts=model_concepts)
