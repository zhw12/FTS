import json
import re
import string
import time

from elasticsearch import Elasticsearch


def index_author_data():
    INDEX_NAME = 'author'
    TYPE_NAME = 'author'
    ES_HOST = '127.0.0.1:9200'
    NUM_OF_SHARDS = 1
    NUM_OF_REPLICAS = 0

    es = Elasticsearch(hosts=[ES_HOST])

    with open('./data/authors.csv') as f:
        author_data = [i for i in f]

    ''' '"authorID","firstName","lastName","email","organizationName","personalHomePageURL","user_id","datasetSource","fullName","gIndex","hIndex","numberOfCitations","numberOfPapers","rawID","fax","phone","address","organization_id"\n'
    '''

    total_authors = len(author_data)
    bulk_data = []
    cnt = 0
    start = time.time()
    batch_size = 10000

    for line in author_data:
        al = line.split('\"')
        email = filter(lambda x: x in string.printable, al[7])
        organization = filter(lambda x: x in string.printable, al[9])
        author = filter(lambda x: x in string.printable, al[17])

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
            print('indexing %d/%d documents...') % (cnt, total_authors)
            print('Indexing data using %s s...' % (end - start))
            bulk_data = []

    if bulk_data:
        es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)
        end = time.time()
        print('indexing %d/%d documents...') % (cnt, total_authors)
        print('Indexing data using %s s...' % (end - start))


if __name__ == '__main__':
    index_author_data()
