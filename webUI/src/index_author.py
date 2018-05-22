import json
import re
import string
import time
import os
from elasticsearch import Elasticsearch

INDEX_NAME = 'author'
TYPE_NAME = 'author'
ES_HOST = '127.0.0.1:9200'
NUM_OF_SHARDS = 1
NUM_OF_REPLICAS = 0

root_dir = os.path.abspath('../..')

def create_author_index():
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
                    "fullName": {"type": "string", "analyzer": "whitespace"},
                    "email": {"type": "string"},
                    "organizationName": {"type": "string"}
                }
            }
        }
    }

    print("creating '%s' index..." % (INDEX_NAME))
    res = es.indices.create(
        index=INDEX_NAME, body=request_body, request_timeout=30)
    print(" response: '%s'" % (res))


def index_author_data():
    es = Elasticsearch(hosts=[ES_HOST])

    with open('{}/data/authors.csv'.format(root_dir)) as f:
        author_data = [i for i in f]

    ''' '"authorID","firstName","lastName","email","organizationName","personalHomePageURL","user_id","datasetSource","fullName","gIndex","hIndex","numberOfCitations","numberOfPapers","rawID","fax","phone","address","organization_id"\n'
    '''

    total_authors = len(author_data)
    bulk_data = []
    cnt = 0
    start = time.time()
    batch_size = 10000

    for line in author_data:
        try:
            al = line.split('\"')
            email = ''.join(filter(lambda x: x in string.printable, al[7]))
            organization = ''.join(filter(lambda x: x in string.printable, al[9]))
            author = ''.join(filter(lambda x: x in string.printable, al[17]))

            op_dict = {
                "index": {
                    "_index": INDEX_NAME,
                    "_type": TYPE_NAME,
                }
            }

            data_dict = {
                'author': author,
                'email': email,
                'organization': organization
            }
            bulk_data.append(op_dict)
            bulk_data.append(data_dict)
            cnt += 1
            if cnt % batch_size == 0:
                es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
                end = time.time()
                print('indexing %d/%d documents...' % (cnt, total_authors))
                print('Indexing data using %s s...' % (end - start))
                bulk_data = []
        except IndexError:
            bulk_data = []

    if bulk_data:
        es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
        end = time.time()
        print('indexing %d/%d documents...' % (cnt, total_authors))
        print('Indexing data using %s s...' % (end - start))


def search_author_data():
    es = Elasticsearch(hosts=[ES_HOST])

    query_body = {
        'size': 10,
        'query': {
            'bool': {
                'must': [
                    {
                        'match': {'author': 'Zhang'}
                    }
                ]
            }
        }
    }

    res = es.search(
        index=INDEX_NAME,
        request_timeout=180,
        body=query_body
    )
    print(res)


if __name__ == '__main__':
    create_author_index()
    index_author_data()
    search_author_data()
