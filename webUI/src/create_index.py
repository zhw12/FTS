from elasticsearch import Elasticsearch

def create_inedx():
    INDEX_NAME = 'taxongen1'
    TYPE_NAME = 'taxongen_docs'
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
                    "title": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "title_exact": {
                        "type": "string",
                        "analyzer": "standard"
                    },
                    "authors": {
                        "type": "string"
                    },
                    "sid": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "keyPhrases": {
                        "type": "string"
                    },
                    "paperAbstract": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "paperAbstract_exact": {
                        "type": "string",
                        "analyzer": "standard"
                    },
                    "text": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "text_exact": {
                        "type": "string",
                        "analyzer": "standard"
                    },
                    "pdfUrl": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "s2Url": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "venue": {
                        "type": "string"
                    },
                    "year": {
                        "type": "long"
                    },
                    "taxonIDs": {
                        "type": "string",
                        "analyzer": "whitespace"
                    },
                    "university": {
                        "type": "string",
                    },
                    "country": {
                        "type": "string",
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
    create_inedx()
