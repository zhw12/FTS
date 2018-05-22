# elasticsearch for retrieve documents
from elasticsearch import Elasticsearch
import re

class ES():
    '''
        elastic search has a limit of size on search, default limit is 10000
        10000 is good enough to get statistics
    '''
    def __init__(self, index_name, type_name, request_timeout=180, size=10000):
        self.INDEX_NAME = index_name
        self.TYPE_NAME = type_name
        self.REQUEST_TIMEOUT = request_timeout
        self.TITLE_WIEGHT = 16
        self.BODY_WEIGHT = 3
        self.SIZE = size
        self.es = Elasticsearch()

    def search_articles_by_common_term(self, phrase, id_only=True):
        search_body = {
            "size": self.SIZE,
            "query": {
                'bool': {
                    'should': [
                        {
                            'common': {
                                'title': {
                                    'query': phrase,
                                    'cutoff_frequency': 0.001,
                                }
                            },
                        },
                        {
                            'common': {
                                'paperAbstract': {
                                    'query': phrase,
                                    'cutoff_frequency': 0.001,
                                }
                            },
                        },
                    ]

                }
            }
        }
        if id_only:
            search_body["_source"] = ["sid"]

        res = self.es.search(index=self.INDEX_NAME, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
        print("Phrase: %s, Total hits = %s" % (phrase, res['hits']['total']))
        total = res['hits']['total']
        id_list = [(hit["_source"]["sid"]) for hit in res["hits"]["hits"]]
        return id_list, total


    def search_articles_by_phrase(self, phrase, id_only=True):
        search_body = {
            "size": self.SIZE,
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase": {"title": {"query": phrase, "boost": self.TITLE_WIEGHT}}},
                        {"match_phrase": {"article": {"query": phrase, "boost": self.BODY_WEIGHT}}}
                    ]
                }
            }
        }
        if id_only:
            search_body["_source"] = ["sid"]

        res = self.es.search(index=self.INDEX_NAME, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
        print("Phrase: %s, Total hits = %s" % (phrase, res['hits']['total']))
        total = res['hits']['total']
        id_list = [(hit["_source"]["sid"]) for hit in res["hits"]["hits"]]
        return id_list, total

    def search_articles_by_ids(self, docids):
        texts = []
        bulk = []
        op_dict = {"index": self.INDEX_NAME, "type": self.TYPE_NAME}
        cnt = 0
        for docid in docids:
            cnt += 1
            search_body = {"query": {"term": {"sid": docid}}}
            bulk.append(op_dict)
            bulk.append(search_body)

            if cnt % 1000 == 0:
                resp = self.es.msearch(body=bulk, request_timeout=self.REQUEST_TIMEOUT)["responses"]
                for res in resp:
                    for hit in res["hits"]["hits"]:
                        if not hit["_source"]:
                            print("Error", hit)
                        # text = hit["_source"]["sid"] + '\t'
                        text = ''
                        text = text + hit["_source"]['title'] + ' ' + hit["_source"]['paperAbstract']
                        text = text.replace('\n', ' ').replace('\r', '')
                        text = text + '\n'
                        texts.append(text)
                # print("Finish generating %s documents" % cnt, end='\r')
                bulk = []
        
        if bulk:
            # save those remaining documents
            resp = self.es.msearch(body=bulk, request_timeout=self.REQUEST_TIMEOUT)["responses"]
            for res in resp:
                for hit in res["hits"]["hits"]:
                    text = ''
                    text = text + hit["_source"]['title'] + ' ' + hit["_source"]['paperAbstract']
                    text = text.replace('\n', ' ').replace('\r', '')
                    text = text + '\n'
                    texts.append(text)
            # print("Finish saving generating %s documents" % int(len(bulk) / 2), end='\r')
        return texts

# utility functions
def rmTag_concat(line):
    def concat(matched):
        phrase = matched.group()
        phrase = re.sub('<phrase>', '', phrase)
        phrase = re.sub('</phrase>', '', phrase)
        return '_'.join(phrase.split())
    if line.startswith('<phrase>'):
        res = re.sub("<phrase>(.*?)</phrase>", concat, line)
    else:
        res = '_'.join(line.split())
    return res

def wrapTag(line):
    if '_' in line or ' ' in line:
        return '<phrase>{}</phrase>'.format(rmTag_concat(line))
    else:
        return line

def rmUnderscore(line):
    return line.replace('_', ' ')

def cleanText(line):
    # \1 is equivalent to re.search(...).group(1)
    line = re.sub(r"([.,!:?()])", r" \1 ", line)
    line = re.sub('\s+', ' ', line)
    line = line.strip()
    return line

# def test_fun():
#     print(2)