from elasticsearch import Elasticsearch

def search_author_data():
    INDEX_NAME = 'author'
    TYPE_NAME = 'author'
    ES_HOST = '127.0.0.1:9200'
    NUM_OF_SHARDS = 1
    NUM_OF_REPLICAS = 0

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
    print (res)

if __name__ == '__main__':
    search_author_data()
