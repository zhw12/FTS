import json
import time
import os
from pathlib import Path

from elasticsearch import Elasticsearch

INDEX_NAME = 'author_doc'
TYPE_NAME = 'author_doc'
ES_HOST = '127.0.0.1:9200'
# root_dir = os.path.abspath('../..')
root_dir = Path(__file__).absolute().parent.parent.parent


def create_inedx():
    NUM_OF_SHARDS = 1
    NUM_OF_REPLICAS = 0

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
                    "author": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "text": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "venue": {
                        "type": "string"
                    },
                    "year": {
                        "type": "long"
                    }
                }
            }
        }
    }

    print("creating '%s' index..." % (INDEX_NAME))
    res = es.indices.create(
        index=INDEX_NAME, body=request_body, request_timeout=30)
    print(" response: '%s'" % (res))


def index_data():
    def file_len(filename):
        cnt = 0
        with open(filename) as fin:
            for _ in fin:
                cnt += 1
        return cnt

    es = Elasticsearch(hosts=[ES_HOST])

    input_file_path = '{}/data/dblp_json_with_taxon.txt'.format(root_dir)
    '''
    A node example:
    {"taxonIDs": "0_0_0,1_6_6,2_45_53,3_170_242", "authors": [{"ids": ["2901822"], "name": "Jarle Berntsen"}, {"ids": ["3065129"], "name": "Terje O. Espelid"}, {"ids": ["1734544"], "name": "Alan Genz"}], "paperAbstract": "An adaptive algorithm for numerical integration ...", "venue": "ACM Trans. Math. Softw.", "pdfUrls": ["http://doi.acm.org/10.1145/210232.210233", "http://www.math.wsu.edu/faculty/genz/papers/cuhre.pdf", "http://www.sci.wsu.edu/math/faculty/genz/papers/cuhre.ps"], "outCitations": ["42fba05549e5bbaa4d5e52948de2694bdd6fc0d5", "eced5bbdff9d80cc9f61d5316412542fde84ad78"], "id": "0067bc2887479de03b07f05642ef22e710452ac5", "inCitations": ["92f55e4c2cf488f0439f071ea73c146b55f62eb6"], "title": "An adaptive algorithm for the approximate calculation of multiple integrals", "keyPhrases": ["Integral", "Subdivision", "Adaptive Algorithm", "Integrand", "Subregion"], "year": 1991, "s2Url": "http://semanticscholar.org/paper/0067bc2887479de03b07f05642ef22e710452ac5"}
    '''

    print('Start indexing data...')
    cnt = 0
    doc_cnt = 0
    batch_size = 10000
    bulk_data = []
    start = time.time()
    total_docs = file_len(input_file_path)
    with open(input_file_path) as f:
        for line in f:
            data = json.loads(line)
            authors = []
            for author in data['authors']:
                authors.append(author['name'])
            op_dict = {
                "index": {
                    "_index": INDEX_NAME,
                    "_type": TYPE_NAME,
                }
            }

            citation_cnt = len(data.get('inCitations', []))

            for author in authors:
                data_dict = {

                    'author': author,
                    'text': data.get('title', '') + ' . ' + data.get('paperAbstract'),
                    'venue': data.get('venue', ''),
                    'year': data.get('year', 0),
                    'citation_cnt': citation_cnt
                }
                bulk_data.append(op_dict)
                bulk_data.append(data_dict)
                cnt += 1
                if cnt % batch_size == 0:
                    es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
                    end = time.time()
                    print('indexing %d/%d documents...' % (cnt, total_docs))
                    print('Indexing data using %s s...' % (end - start))
                    bulk_data = []

    if bulk_data:
        es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
        end = time.time()
        print('indexing %d/%d documents...' % (cnt, total_docs))
        print('Indexing data using %s s...' % (end - start))

if __name__ == '__main__':
    create_inedx()
    index_data()
    # search_data()
