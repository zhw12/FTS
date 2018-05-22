'''
__author__: Jiaming Shen
__description__: The helper class for create index, index data, and search from index, using Elasticsearch 5.4.0
__latest_update__: 10/14/2017
'''
import time
from elasticsearch import Elasticsearch

class ES():
  def __init__(self, topK=20, request_timeout=180):
    ''' Elasticsearch configuration parameters
    '''

    self.topK = topK # top returned results
    self.REQUEST_TIMEOUT = request_timeout  # timeout limit in second
    self.NUMBER_SHARDS = 1 # keep this as 1 if no cluster is used
    self.NUMBER_REPLICAS = 0 # keep this as 0 if no cluster is used
    self.es = Elasticsearch()

  def check_existing_index(self, index_name, delete_existing=False):
    if self.es.indices.exists(index = index_name):
      print("[INFO] Index: %s exists" % index_name)
      if delete_existing:
        res = self.es.indices.delete(index = index_name)
        print("[INFO] Deleting index %s , Response: %s" % (index_name, res))
      else:
        print("[INFO] Using existing index %s" % index_name)
      return True
    else:
      return False

  def create_skipgram2eid_index(self, index_name, type_name):
    request_body = {
      "settings": {
        "number_of_shards": self.NUMBER_SHARDS,
        "number_of_replicas": self.NUMBER_REPLICAS,
      },
      "mappings": {
        type_name: {
          "properties": {
            "skipgram": {"type": "keyword"},
            "skipgramID": {"type": "keyword"},
            "skipgramPop": {"type": "long"}, # number of occurrence of this skipgram
            "skipgramDist": {"type": "long"}, # number of distinct eids this skipgram matches
            "eid_tfidf": {"type": "text","similarity": "classic"},
            "eid_bm25": {"type": "text", "similarity": "BM25"}
          }
        }
      }
    }

    if self.es.indices.exists(index = index_name):
      print("[INFO] Index: %s exists" % index_name)
    else:
      res = self.es.indices.create(index=index_name, body=request_body)
      print("[INFO] Create index %s , Response: %s" % (index_name, res))

  def create_eid2skipgram_index(self, index_name, type_name):
    request_body = {
      "settings": {
        "number_of_shards": self.NUMBER_SHARDS,
        "number_of_replicas": self.NUMBER_REPLICAS,
      },
      "mappings": {
        type_name: {
          "properties": {
            "eid": {"type": "keyword"},
            "eidPop": {"type": "long"}, # number of total occurrence of this eid
            "eidDist": {"type": "long"}, # number of distinct skipgram this eid matches
            "skipgrams": {"type": "text", "similarity": "BM25"}
          }
        }
      }
    }

    if self.es.indices.exists(index = index_name):
      print("[INFO] Index: %s exists" % index_name)
    else:
      res = self.es.indices.create(index = index_name, body=request_body)
      print("[INFO] Create index %s , Response: %s" % (index_name, res))

  def create_eid2eid_index(self, index_name, type_name):
    request_body = {
      "settings": {
        "number_of_shards": self.NUMBER_SHARDS,
        "number_of_replicas": self.NUMBER_REPLICAS,
      },
      "mappings": {
        type_name: {
          "properties": {
            "eid": {"type": "keyword"},
            "related_eids": {"type": "text", "similarity": "BM25"}
          }
        }
      }
    }

    if self.es.indices.exists(index = index_name):
      print("[INFO] Index: %s exists" % index_name)
    else:
      res = self.es.indices.create(index = index_name, body=request_body)
      print("[INFO] Create index %s , Response: %s" % (index_name, res))

  def index_skipgram2eid(self, index_name, type_name, skipgram2id, skipgram2eidcounts):
    start = time.time()
    bulk_size = 10000  # number of skipgram processed in each bulk
    bulk_data = []  # data in bulk

    cnt = 0
    for skipgram in skipgram2id:
      cnt += 1
      skipgramID = "sg" + str(skipgram2id[skipgram])
      eidcounts = skipgram2eidcounts[skipgram]
      skipgramPop = sum([ele[1] for ele in eidcounts])
      skipgramDist = len(eidcounts)
      eidcounts_string = " ".join([" ".join([ele[0]]*ele[1]) for ele in eidcounts])

      data_dict = {}
      data_dict["skipgram"] = skipgram
      data_dict["skipgramID"] = skipgramID
      data_dict["skipgramPop"] = skipgramPop
      data_dict["skipgramDist"] = skipgramDist
      data_dict["eid_tfidf"] = eidcounts_string
      data_dict["eid_bm25"] = eidcounts_string

      ## Put current data into the bulk
      op_dict = {"index": {"_index": index_name, "_type": type_name, "_id": data_dict["skipgramID"]}}

      bulk_data.append(op_dict)
      bulk_data.append(data_dict)

      ## Start Bulk indexing
      if cnt % bulk_size == 0 and cnt != 0:
        tmp = time.time()
        self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
        print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))
        bulk_data = []

    ## indexing those left skipgrams
    if bulk_data:
      tmp = time.time()
      self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
      print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))

    end = time.time()
    print("Finish %s skipgrams indexing. Total escaped time %s (seconds) " % (index_name, (end - start)))

  def index_eid2skipgram(self, index_name, type_name, eid2skipgramcounts):
    start = time.time()
    bulk_size = 500  # number of eid processed in each bulk
    bulk_data = []  # data in bulk

    cnt = 0
    for eid in eid2skipgramcounts:
      cnt += 1
      skipgramcounts = eid2skipgramcounts[eid]
      eidPop = sum([ele[1] for ele in skipgramcounts])
      eidDist = len(skipgramcounts)
      skipgramcounts_string = " ".join([" ".join(["sg"+str(ele[0])]*ele[1]) for ele in skipgramcounts])

      data_dict = {}
      data_dict["eid"] = eid
      data_dict["eidPop"] = eidPop
      data_dict["eidDist"] = eidDist
      data_dict["skipgrams"] = skipgramcounts_string

      ## Put current data into the bulk
      op_dict = {"index": {"_index": index_name, "_type": type_name, "_id": data_dict["eid"]}}

      bulk_data.append(op_dict)
      bulk_data.append(data_dict)

      ## Start Bulk indexing
      if cnt % bulk_size == 0 and cnt != 0:
        tmp = time.time()
        self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
        print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))
        bulk_data = []

    ## indexing those left eid
    if bulk_data:
      tmp = time.time()
      self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
      print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))

    end = time.time()
    print("Finish %s eid indexing. Total escaped time %s (seconds) " % (index_name, (end - start)))

  def index_eid2eid(self, index_name, type_name, eid2eid_w_strength):
    start = time.time()
    bulk_size = 500  # number of eid processed in each bulk
    bulk_data = []  # data in bulk

    cnt = 0
    for eid in eid2eid_w_strength:
      cnt += 1
      eid_w_strength = eid2eid_w_strength[eid]
      eids_string = " ".join([" ".join([str(ele[0])] * ele[1]) for ele in eid_w_strength.items()])

      data_dict = {}
      data_dict["eid"] = eid
      data_dict["related_eids"] = eids_string

      ## Put current data into the bulk
      op_dict = {"index": {"_index": index_name, "_type": type_name, "_id": data_dict["eid"]}}

      bulk_data.append(op_dict)
      bulk_data.append(data_dict)

      ## Start Bulk indexing
      if cnt % bulk_size == 0 and cnt != 0:
        tmp = time.time()
        self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
        print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))
        bulk_data = []

    ## indexing those left eid
    if bulk_data:
      tmp = time.time()
      self.es.bulk(index=index_name, body=bulk_data, request_timeout=180)
      print("bulk indexing... %s, escaped time %s (seconds) " % (cnt, tmp - start))

    end = time.time()
    print("Finish %s eid indexing. Total escaped time %s (seconds) " % (index_name, (end - start)))

  def search_sgid_by_eid(self, index_name, type_name, topK, eid_list, lower_bound=0, upper_bound=1000, DEBUG=False):
    query_string = " ".join([str(ele) for ele in eid_list])
    search_body = {
      "size": topK,
      "_source": ["skipgram", "skipgramID", "skipgramPop", "skipgramDist"],
      "query": {
        "bool": {
          "must": {
            "range": {
              "skipgramDist": {"gte": lower_bound, "lte": upper_bound}
            }
          },
          "should": [
            {
              "match": {"eid_tfidf": query_string}
            }
          ]
        }
      }
    }
    res = self.es.search(index=index_name, doc_type=type_name, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
    if DEBUG:
      for hit in res["hits"]["hits"]:
        skipgram = hit["_source"]["skipgram"]
        skipgramID = hit["_source"]["skipgramID"]
        skipgramDist = hit["_source"]["skipgramDist"]
        skipgramPop = hit["_source"]["skipgramPop"]
        score = hit["_score"]
        print("Skipgram: %s (id=%s), Score: %s, Dist: %s, Pop: %s" % (skipgram, skipgramID, score, skipgramDist, skipgramPop))
      skipgramIDs = [hit["_source"]["skipgramID"] for hit in res["hits"]["hits"]]
    else:
      skipgramIDs = [hit["_source"]["skipgramID"] for hit in res["hits"]["hits"]]
    return skipgramIDs

  def search_by_sgid(self, index_name, type_name, topK, sgid_list, eidename, DEBUG=False):
    query_string = " ".join(sgid_list)
    search_body = {
      "size": topK,
      "_source": False,
      "query": {
        "match": {
          "skipgrams": query_string
        }
      }
    }
    res = self.es.search(index=index_name, doc_type=type_name, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
    if DEBUG:
      for hit in res["hits"]["hits"]:
        eid = int(hit["_id"])
        score = hit["_score"]
        print("Eid: %s, Ename: %s, Score: %s" % (eid, eidename[eid], score))
      expanded_eids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
    else:
      expanded_eids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
    return expanded_eids

  def search_eid_by_eid(self, index_name, type_name, topK, eid_list, eidename, DEBUG=False):
    query_string = " ".join([str(ele) for ele in eid_list])
    search_body = {
      "size": topK,
      "_source": False,
      "query": {
        "match": {
          "related_eids": query_string
        }
      }
    }
    res = self.es.search(index=index_name, doc_type=type_name, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
    if DEBUG:
      for hit in res["hits"]["hits"]:
        eid = int(hit["_id"])
        score = hit["_score"]
        print("Eid: %s, Ename: %s, Score: %s" % (eid, eidename[eid], score))
      expanded_eids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
    else:
      expanded_eids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
    return expanded_eids

  def match_all(self, index_name, type_name):
    ''' Used to obtain a random set of records from index. For testing purpose only.

    :param index_name:
    :param type_name:
    :return:
    '''
    search_body = {"query": {"match_all": {}}}
    res = self.es.search(index=index_name, doc_type=type_name, request_timeout=self.REQUEST_TIMEOUT, body=search_body)
    for hit in res["hits"]["hits"]:
      print(hit["_score"])
      print(hit)