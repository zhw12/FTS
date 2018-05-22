from elasticsearch import Elasticsearch
import json

def create_country_index():
    INDEX_NAME = 'country'
    TYPE_NAME = 'country'
    ES_HOST = '127.0.0.1:9200'
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

if __name__ == '__main__':
    create_country_index()
