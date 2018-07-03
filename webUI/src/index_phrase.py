import os
import re
import time
from pathlib import Path

from elasticsearch import Elasticsearch
from gensim.models import word2vec

# root_dir = '/home/hanwen/disk/demov3'
# root_dir = os.path.abspath('../..')
root_dir = Path(__file__).absolute().parent.parent.parent

def displayString(w):
    return re.sub(r'</?phrase>', '', w).replace('_', ' ').replace('-', ' ')


def wrap_marker(w):
    return '<phrase>%s</phrase>' % w.replace(' ', '_')


def is_phrase(w):
    return w.startswith('<phrase>') and w.endswith('</phrase>')


INDEX_NAME = 'phrase1'
TYPE_NAME = 'phrase'
ES_HOST = '127.0.0.1:9200'
NUM_OF_SHARDS = 1
NUM_OF_REPLICAS = 0


def create_phrase_index():
    es = Elasticsearch(hosts=[ES_HOST])

    if es.indices.exists(INDEX_NAME):
        print("deleting '%s' index..." % (INDEX_NAME))
        res = es.indices.delete(index=INDEX_NAME)
        print(" response: '%s'" % (res))

    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            TYPE_NAME: {
                "properties": {
                    "phrase": {"type": "completion", "analyzer": "whitespace"},
                }
            }
        }
    }

    print("creating '%s' index..." % (INDEX_NAME))
    res = es.indices.create(
        index=INDEX_NAME, body=request_body, request_timeout=30)
    print(" response: '%s'" % (res))


def index_phrase_data():
    es = Elasticsearch(hosts=[ES_HOST])
    # file_wordvec = '{}/concept_based_retrieval/output/SEMANTIC_SCHOLAR120w/wordvec'.format(root_dir)
    file_wordvec = '{}/embedding/wordvec'.format(root_dir)
    model_concepts = word2vec.Word2Vec.load(file_wordvec)

    phrase_list = []
    for w in model_concepts.wv.vocab:
        if is_phrase(w) and wrap_marker(displayString(w)) == w:
            phrase_list.append(displayString(w))

    total_phrases = len(phrase_list)
    bulk_data = []
    cnt = 0
    start = time.time()
    batch_size = 10000

    for phrase in phrase_list:
        op_dict = {
            "index": {
                "_index": INDEX_NAME,
                "_type": TYPE_NAME,
            }
        }
        data_dict = {
            'phrase': phrase,
        }
        bulk_data.append(op_dict)
        bulk_data.append(data_dict)
        cnt += 1
        if cnt % batch_size == 0:
            es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
            end = time.time()
            print('indexing %d/%d documents...' % (cnt, total_phrases))
            print('Indexing data using %s s...' % (end - start))
            bulk_data = []

    if bulk_data:
        es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
        end = time.time()
        print('indexing %d/%d documents...' % (cnt, total_phrases))
        print('Indexing data using %s s...' % (end - start))


def search_data():
    topK = 10

    es = Elasticsearch(hosts=[ES_HOST])

    query = 'deep'
    suggDoc = {
        "suggest": {
            'prefix': query,
            "completion": {
                "field": 'phrase',
                "size": topK
            }
        },
    }

    res = es.suggest(body=suggDoc, index=INDEX_NAME, request_timeout=180)

    print(res)


if __name__ == '__main__':
    create_phrase_index()
    index_phrase_data()
    search_data()
