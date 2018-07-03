import json
import os
import time
from pathlib import Path

from elasticsearch import Elasticsearch

INDEX_NAME = 'country'
TYPE_NAME = 'country'
ES_HOST = '127.0.0.1:9200'
NUM_OF_SHARDS = 1
NUM_OF_REPLICAS = 0

# root_dir = os.path.abspath('../..')
root_dir = Path(__file__).absolute().parent.parent.parent

def create_country_index():
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
                    "university": {
                        "type": "string"
                    },
                    "country": {
                        "type": "string"
                    }
                }
            }
        }
    }

    print("creating '%s' index..." % (INDEX_NAME))
    res = es.indices.create(
        index=INDEX_NAME, body=request_body, request_timeout=30)
    print(" response: '%s'" % (res))


def index_country_data():
    es = Elasticsearch(hosts=[ES_HOST])

    with open('{}/data/uni2cty.json'.format(root_dir), 'r') as f:
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

    es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout=180)


def search_country_data():
    es = Elasticsearch(hosts=[ES_HOST])

    query_body = {
        'size': 10,
        'query': {
            'bool': {
                'must': [
                    {
                        'match': {'country': 'United'}
                        # 'match': {'university': 'University of Illinois, Urbana, Ill. (U.S.A.)'}
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
    create_country_index()
    index_country_data()
    time.sleep(1)
    search_country_data()
