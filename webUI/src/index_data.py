import time
from elasticsearch import Elasticsearch
import json


def index_data():
    INDEX_NAME = 'taxongen1'
    TYPE_NAME = 'taxongen_docs'
    ES_HOST = '127.0.0.1:9200'

    es = Elasticsearch(hosts=[ES_HOST])

    input_file_path = './TaxonGen/data/dblp2/dblp_json_with_taxon.txt'
    doc_country_file_path = './data/doc_country.txt'

    '''
    A node example:
    {"taxonIDs": "0_0_0,1_6_6,2_45_53,3_170_242", "authors": [{"ids": ["2901822"], "name": "Jarle Berntsen"}, {"ids": ["3065129"], "name": "Terje O. Espelid"}, {"ids": ["1734544"], "name": "Alan Genz"}], "paperAbstract": "An adaptive algorithm for numerical integration ...", "venue": "ACM Trans. Math. Softw.", "pdfUrls": ["http://doi.acm.org/10.1145/210232.210233", "http://www.math.wsu.edu/faculty/genz/papers/cuhre.pdf", "http://www.sci.wsu.edu/math/faculty/genz/papers/cuhre.ps"], "outCitations": ["42fba05549e5bbaa4d5e52948de2694bdd6fc0d5", "eced5bbdff9d80cc9f61d5316412542fde84ad78"], "id": "0067bc2887479de03b07f05642ef22e710452ac5", "inCitations": ["92f55e4c2cf488f0439f071ea73c146b55f62eb6"], "title": "An adaptive algorithm for the approximate calculation of multiple integrals", "keyPhrases": ["Integral", "Subdivision", "Adaptive Algorithm", "Integrand", "Subregion"], "year": 1991, "s2Url": "http://semanticscholar.org/paper/0067bc2887479de03b07f05642ef22e710452ac5"}
    '''

    print('Start indexing data...')
    cnt = 0
    batch_size = 10000
    bulk_data = []
    start = time.time()
    total_docs = 1225509
    with open(input_file_path) as f, open(doc_country_file_path) as fc:
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
            if line_c:
                country, university = line_c.split('\t')
            else:
                university = ''
                country = ''
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

            data_dict = {
                'taxonIDs': data['taxonIDs'].replace(',', ' '),
                'title': data.get('title', ''),
                'title_exact': data.get('title', ''),
                'authors': authors,
                'sid': data['id'],
                'keyPhrases': data.get('keyPhrases'),
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
                es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout = 180)
                end = time.time()
                print('indexing %d/%d documents...') % (cnt, total_docs)
                print('Indexing data using %s s...'%(end-start))
                bulk_data = []

    if bulk_data:
        es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout = 180)
        end = time.time()
        print('indexing %d/%d documents...') % (cnt, total_docs)
        print('Indexing data using %s s...'%(end-start))

if __name__ == '__main__':
    index_data()
