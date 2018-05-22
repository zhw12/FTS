from elasticsearch import Elasticsearch

def search_country_data():
    INDEX_NAME = 'country'
    TYPE_NAME = 'country'
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
                        # 'match': {'country': 'United States'}
                        'match': {'university': 'University of Illinois, Urbana, Ill. (U.S.A.)'}
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
    search_country_data()
