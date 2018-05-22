# import requests
import json
from elasticsearch import Elasticsearch
import time

def index_country_data():
    INDEX_NAME = 'country'
    TYPE_NAME = 'country'
    ES_HOST = '127.0.0.1:9200'
    NUM_OF_SHARDS = 1
    NUM_OF_REPLICAS = 0

    es = Elasticsearch(hosts=[ES_HOST])

    with open('./data/uni2cty.json', 'r') as f:
        university_dict = json.load(f)
    print(len(university_dict))

    bulk_data = []
    for u in university_dict:
        op_dict = {
            "index": {
                "_index": INDEX_NAME,
                "_type": TYPE_NAME,
                }
            }

        data_dict = {
            'country': university_dict[u],
            'university': u
        }
        bulk_data.append(op_dict)
        bulk_data.append(data_dict)

    es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout = 180)

if __name__ == '__main__':
    index_country_data()
