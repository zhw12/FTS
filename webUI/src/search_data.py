from elasticsearch import Elasticsearch

def search_data():
    INDEX_NAME = 'taxongen'
    TYPE_NAME = 'taxongen_docs'
    ES_HOST = '127.0.0.1:9200'
    topK = 10

    es = Elasticsearch(hosts=[ES_HOST])

    # query_body = {
    #     'size': topK,
    #     'query': {
    #         'bool': {
    #             'must': [
    #                 # {
    #                 #     'match': {'title': ''}
    #                 # },
    #                 {
    #                     'match': {'taxonIDs': '0_0_0'}
    #                 },
    #                 {
    #                     'range': {
    #                         'year': {
    #                             'gte': '2007',
    #                             'lte': '2009',
    #                             'format': 'yyyy||yyyy'
    #                         }
    #                     }
    #                 }
    #             ]
    #         },
    #     }
    # }

    query_body = {
        'size': 1,
        'query': {
            'bool': {
                'must': [
                    {
                        'match': {'taxonIDs': '0_0_0'}
                    },
                    # {
                    #     "match_phrase" : {
                    #         "paperAbstract" : "data mining"
                    #     }
                    # }
                    {
                        "common": {
                            "country": {
                                "query": "United States",
                                    "cutoff_frequency": 0.001
                            }
                        }
                    }

                    # {
                    #     'bool': {
                    #         'should': [
                    #             {
                    #                 'match': {
                    #                     'title': {
                    #                         'query': 'deep learning',
                    #                         'boost': 2
                    #                     }
                    #                 },
                    #                 'match': {
                    #                     'paperAbstract': {
                    #                         'query': 'deep learning',
                    #                         'boost': 2
                    #                     }
                    #                 },
                    #             },
                    #         ]
                    #
                    #     }
                    # }


                ],
                'should': [

                    # {
                    #     'match': {'paperAbstract': 'learning'}
                    # },
                ]
            },
        },
        'aggs': {
            'year': {
                'terms': {
                  'field': 'year',
                  'size': 100
                }
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
    search_data()
