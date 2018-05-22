'''
__author__: Jiaming Shen
__description__: One time using
'''
import time
import re
from elasticsearch import Elasticsearch
import numpy as np
import json

def bulk_index(bulk_data, cnt, start):
    # print('indexing %d documents...' % (len(bulk_data)/2))
    es.bulk(index=INDEX_NAME, body=bulk_data, request_timeout = 180)
    end = time.time()
    print('Indexed %s papers using %s s...' % (cnt, (end-start) ) )

if __name__ == '__main__':
    input_dblp_path = "/shared/data/jiaming/local-embedding/data/dblp/input/papers.txt"
    input_doc_id_path = "/shared/data/jiaming/local-embedding/data/dblp/init/doc_ids.txt"
    output_dblp_path = "/shared/data/jiaming/semantic_scholar/dblp/dblp_semantic_scholar.txt"

    INDEX_NAME = 'semantic_scholar'
    TYPE_NAME = 'semantc_scholar_docs'
    ES_HOST = '127.0.0.1:9200'
    # skipcount = 1035500 # reindex from here

    start = time.time()
    es = Elasticsearch(hosts=[ES_HOST])
    cnt = 0
    buffer_cnt = 0
    bulk = []
    bulk_size = 500
    with open(input_dblp_path,"r") as fin, open(output_dblp_path, "w") as fout:
      for line in fin:
        line = line.strip()
        query = re.sub("_"," ", line)
        word_cnt = len(query.split())
        if word_cnt > 100:
          query = " ".join(query.split()[:100])

        search_body = {"size": 1, "_source": ["sid"], "query": {"match": {"title": query}}}
        op_dict = {
          "index": INDEX_NAME,
          "type": TYPE_NAME
        }
        bulk.append(op_dict)
        bulk.append(search_body)

        cnt += 1
        buffer_cnt += 1
        if cnt % bulk_size == 0:
          # if cnt <= skipcount: # skip all already indexed documents
          #   bulk = []
          #   buffer_cnt = 0
          #   continue

          resp = es.msearch(body=bulk, request_timeout=180)["responses"]
          for idx,res in enumerate(resp):
            if res and len(res["hits"]["hits"]) > 0:
              fout.write(str(cnt-bulk_size+idx) + "\t" + res["hits"]["hits"][0]["_source"]["sid"] + "\n")
            else:
              fout.write(str(cnt-bulk_size+idx) + "\t" + "-1" + "\n")
              print("Fail to get a paper")

          end = time.time()
          print("Finish aligning %s papers using %s seconds" % (cnt, (end - start)))
          bulk = []
          buffer_cnt = 0
          # break

      resp = es.msearch(body=bulk)["responses"]
      for idx,res in enumerate(resp):
        if res and len(res["hits"]["hits"]) > 0:
          fout.write(str(cnt-buffer_cnt+idx) + "\t" + res["hits"]["hits"][0]["_source"]["sid"] + "\n")
        else:
          fout.write(str(cnt-buffer_cnt+idx) + "\t" + "-1" + "\n")
          print("Fail to get a paper")

      end = time.time()
      print("Finish aligning %s papers using %s seconds" % (cnt, (end - start)))
      bulk = []