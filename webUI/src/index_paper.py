import json
import time
import os
from pathlib import Path

from elasticsearch import Elasticsearch

INDEX_NAME = 'taxongen1'
TYPE_NAME = 'taxongen_docs'
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
                    "autoPhrase1": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "autoPhrase2": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "autoPhrase3": {
                        "type": "string",
                        "index": "not_analyzed"
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


def index_data():
    def file_len(filename):
        cnt = 0
        with open(filename) as fin:
            for _ in fin:
                cnt += 1
        return cnt

    es = Elasticsearch(hosts=[ES_HOST])

    input_file_path = '{}/data/dblp_json_with_taxon.txt'.format(root_dir)
    doc_country_file_path = '{}/data/doc_country.txt'.format(root_dir)
    segged_phrases_file_path = '{}/data/dblpss_120w_segged_phrases.txt'.format(root_dir)

    '''
    A node example:
    {"taxonIDs": "0_0_0,1_6_6,2_45_53,3_170_242", "authors": [{"ids": ["2901822"], "name": "Jarle Berntsen"}, {"ids": ["3065129"], "name": "Terje O. Espelid"}, {"ids": ["1734544"], "name": "Alan Genz"}], "paperAbstract": "An adaptive algorithm for numerical integration ...", "venue": "ACM Trans. Math. Softw.", "pdfUrls": ["http://doi.acm.org/10.1145/210232.210233", "http://www.math.wsu.edu/faculty/genz/papers/cuhre.pdf", "http://www.sci.wsu.edu/math/faculty/genz/papers/cuhre.ps"], "outCitations": ["42fba05549e5bbaa4d5e52948de2694bdd6fc0d5", "eced5bbdff9d80cc9f61d5316412542fde84ad78"], "id": "0067bc2887479de03b07f05642ef22e710452ac5", "inCitations": ["92f55e4c2cf488f0439f071ea73c146b55f62eb6"], "title": "An adaptive algorithm for the approximate calculation of multiple integrals", "keyPhrases": ["Integral", "Subdivision", "Adaptive Algorithm", "Integrand", "Subregion"], "year": 1991, "s2Url": "http://semanticscholar.org/paper/0067bc2887479de03b07f05642ef22e710452ac5"}
    '''

    print('Start indexing data...')
    cnt = 0
    batch_size = 10000
    bulk_data = []
    start = time.time()
    total_docs = file_len(input_file_path)
    with open(input_file_path) as f, open(doc_country_file_path) as fc, open(segged_phrases_file_path) as fs:
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
            line_c = fc.readline()[:-1]
            # if line_c:
            try:
                country, university = line_c.split('\t', 1)
            except ValueError:
                university = ''
                country = ''
            # else:
            #     university = ''
            #     country = ''
            # if not authors:
            #     country = ''
            #     university = ''
            # else:
            #     # print authors
            #     a1 = authors[0]
            #
            #     r1 = es.search(
            #         index='author',
            #         request_timeout=180,
            #         body={
            #             'size': 1,
            #             'query': {
            #                     'match': {'author': a1}
            #             }
            #         }
            #     )
            #     if r1['hits']['total'] == 0:
            #         country = ''
            #         university = ''
            #     else:
            #         university = r1['hits']['hits'][0]['_source']['organization']
            #         r = es.search(
            #             index='country',
            #             request_timeout=180,
            #             body={
            #                 'size': 1,
            #                 'query': {
            #                     'bool': {
            #                         'must': [
            #                             {
            #                                 'match': {'university': university}
            #                             }
            #                         ]
            #                     }
            #                 }
            #             }
            #         )
            #         if r['hits']['total'] == 0:
            #             country = ''
            #         else:
            #             country = r['hits']['hits'][0]['_source']['country']

            line_s = fs.readline()[:-1]
            autoPhrases = [''] * 3
            for i, phrase in enumerate(line_s.split('\t')):
                if i >= 3:
                    break
                autoPhrases[i] = phrase

            data_dict = {
                'taxonIDs': data['taxonIDs'].replace(',', ' '),
                'title': data.get('title', ''),
                'title_exact': data.get('title', ''),
                'authors': authors,
                'sid': data['id'],
                'keyPhrases': data.get('keyPhrases'),
                'autoPhrase1': autoPhrases[0],
                'autoPhrase2': autoPhrases[1],
                'autoPhrase3': autoPhrases[2],
                'paperAbstract': data.get('paperAbstract'),
                'paperAbstract_exact': data.get('paperAbstract'),
                'text': data.get('title', '') + ' . ' + data.get('paperAbstract'),
                'text_exact': data.get('title', '') + ' . ' + data.get('paperAbstract'),
                'pdfUrl': data.get('pdfUrls'),
                's2Url': data.get('s2Url', ''),
                'venue': data.get('venue', ''),
                'year': data.get('year', 0),
                'university': university,
                'country': country
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


def search_data():
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
    print(res)


if __name__ == '__main__':
    create_inedx()
    index_data()
    search_data()
