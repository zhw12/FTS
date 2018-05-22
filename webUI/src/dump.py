import re
import time
import json

from elasticsearch import Elasticsearch

def index_data():
    start = time.time()
    INDEX_NAME = 'taxongen'
    TYPE_NAME = 'taxongen_docs'
    ES_HOST = '127.0.0.1:9200'

    es = Elasticsearch(hosts=[ES_HOST])

    input_file_path = '../TaxonGen/data/dblp2/dblp_json_with_taxon.txt'


    print('Start indexing data...')
    cnt = 0
    batch_size = 10000
    bulk_data = []
    start = time.time()
    total_docs = 1225509
    ff = open('res.txt', 'w')
    with open(input_file_path) as f:
        for line in f:
            data = json.loads(line)

            authors = []
            for author in data['authors']:
                authors.append(author['name'])
            if not authors:
                country = ''
                univeristy = ''
            else:
                a1 = authors[0]

                r1 = es.search(
                    index='author',
                    request_timeout=180,
                    body={
                        'size': 1,
                        'query': {
                                'match': {'author': a1}
                        }
                    }
                )
                if r1['hits']['total'] == 0:
                    country = ''
                    univeristy = ''
                else:
                    univeristy = r1['hits']['hits'][0]['_source']['organization']
                    r = es.search(
                        index='country',
                        request_timeout=180,
                        body={
                            'size': 1,
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {'university': univeristy}
                                        }
                                    ]
                                }
                            }
                        }
                    )
                    if r['hits']['total'] == 0:
                        country = ''
                    else:
                        country = r['hits']['hits'][0]['_source']['country']

            res = country + '\t' + univeristy + '\n'

            ff.write(res)
            if(cnt%batch_size==0):
                end = time.time()
                print('finishing %d docs, using %ss ...'%(cnt, end-start))
            cnt += 1
    ff.close()

if __name__ == '__main__':
    index_data()
