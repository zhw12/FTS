'''
__author__: Jiaming Shen
__description__: Elasticsearch based SetExpan
__latest_update__: 10/15/2017
'''
import sys
sys.path.append('./webUI/SetExpan')
from es import ES
import util
import time
import random
from collections import defaultdict

FLAGS_FIRST_RUN = True
FLAGS_CORPUS_NAME = "wiki2"

eidSkipgramFilePath = "./data/wiki_eidSkipgramCounts.txt"
eidEnameFilePath = "./data/wiki_entity2id.txt"
eidTypeFilePath = "./data/wiki_linked_results.txt"

class SetExpanParams():
  def __init__(self, index_name, max_iter=10, ensemble_batch=10, num_of_top_skipgrams=150, num_of_top_candidate_eids=30,
               feature_subset_size_ratio=0.6, average_rank=10, skipgramDistLower=3, skipgramDistUpper=30,
               use_type=True, parallel_ensemble=True):
    self.index_name = index_name
    self.max_iter = max_iter
    self.ensemble_batch = ensemble_batch
    self.num_of_top_skipgrams = num_of_top_skipgrams
    self.num_of_top_candidate_eids = num_of_top_candidate_eids
    self.feature_subset_size_ratio = feature_subset_size_ratio
    self.average_rank = average_rank
    self.skipgramDistLower = skipgramDistLower
    self.skipgramDistUpper = skipgramDistUpper
    self.use_type = use_type
    self.parallel_ensemble = parallel_ensemble

## Main function of setExpan
def setExpan(es, seedEidsWithConfidence, negativeSeedEids, eid2ename, eid2types, params, FLAGS_DEBUG=False):

  ## Fix random seed for testing
  random.seed(1234567)

  seedEids = [ele[0] for ele in seedEidsWithConfidence]
  eid2confidence = {ele[0]: ele[1] for ele in seedEidsWithConfidence}

  ## Cache the initial seedEids for later use
  cached_initial_seedEids = set([ele for ele in seedEids])

  iters = 0
  stop_iter = 0
  while iters < params.max_iter:
    iters += 1
    print("SetExpan++, iteration %s" % iters)
    prev_seeds = set(seedEids)

    ## Context Feature Selection
    skipgramIDs = es.search_sgid_by_eid(index_name=params.index_name, type_name="skipgram2eid",
                                        topK=params.num_of_top_skipgrams, eid_list=seedEids,
                                        lower_bound=params.skipgramDistLower, upper_bound=params.skipgramDistUpper,
                                        DEBUG=False)

    if params.use_type:
      type2strength = defaultdict(float)
      for eid in seedEids:
        for k,v in eid2types[eid].items():
          type2strength[k] += v
      sorted_types = sorted(type2strength.items(), key = lambda x:-x[1])
      print("CoreTypes:", sorted_types[0:5])
      coreType = sorted_types[0][0]


    ## Rank Ensemble
    eid2mrr = defaultdict(float)
    sampleSize = int(len(skipgramIDs) * params.feature_subset_size_ratio)
    if not params.parallel_ensemble:
      for i in range(params.ensemble_batch):
        sampledCoreSkipgrams = random.sample(skipgramIDs, sampleSize)
        # expanded_eids = es.search_by_sgid(index_name=params.index_name, type_name="eid2skipgram",
        #                                   topK=params.num_of_top_candidate_eids, sgid_list=sampledCoreSkipgrams,
        #                                   eidename=eid2ename,DEBUG=True)
        expanded_eids = es.search_eid_by_eid(index_name=params.index_name, type_name="eid2eid", topK=params.num_of_top_candidate_eids,
                             eid_list = seedEids, eidename=eid2ename, DEBUG=False)
        rank = 0
        for eid in expanded_eids:
          if eid not in prev_seeds:
            if not params.use_type:
              rank += 1
              eid2mrr[eid] += 1.0 / rank
            else: # use type
              if coreType in eid2types.setdefault(eid, {}):
                rank += 1
                eid2mrr[eid] += 1.0 / rank
    else:
      ## Parallel version
      bulk = []
      for i in range(params.ensemble_batch):
        # sampledCoreSkipgrams = random.sample(skipgramIDs, sampleSize)
        query_string = " ".join([str(ele) for ele in seedEids])
        search_body = {"size": params.num_of_top_candidate_eids, "_source": False,
                       "query": {"match": {"related_eids": query_string}}}
        op_dict = {"index": params.index_name, "type": "eid2eid"}
        bulk.append(op_dict)
        bulk.append(search_body)

      resp = es.es.msearch(body=bulk, request_timeout=180)["responses"]
      for idx, res in enumerate(resp):
        expanded_eids = [int(hit["_id"]) for hit in res["hits"]["hits"]]
        rank = 0
        for eid in expanded_eids:
          if eid not in prev_seeds:
            if not params.use_type:
              rank += 1
              eid2mrr[eid] += 1.0 / rank
            else: # use type
              if coreType in eid2types.setdefault(eid, {}):
                rank += 1
                eid2mrr[eid] += 1.0 / rank

    ## Entity Selection
    mrr_threshold = 1.0 * params.ensemble_batch / params.average_rank

    for ele in sorted(eid2mrr.items(), key=lambda x: -x[1]):
      eid = ele[0]
      mrr_score = ele[1]
      if mrr_score < mrr_threshold:
        break
      if eid not in negativeSeedEids:
        seedEids.append(eid)
        eid2confidence[eid] = mrr_score
        if FLAGS_DEBUG:
          print("Add entity %s with mrr score %s" % (eid2ename[eid], mrr_score))

    ## Check termination criterion
    if len(set(seedEids).difference(prev_seeds)) == 0 and len(prev_seeds.difference(set(seedEids))) == 0:
      print("[INFO] Terminated due to no additional quality entities at iteration %s" % iters)
      stop_iter = iters
      break

  if iters >= params.max_iter:
    stop_iter = params.max_iter

  expanded = []
  for eid in seedEids:
    if eid not in cached_initial_seedEids:
      expanded.append([eid, eid2ename[eid], eid2confidence[eid]])

  return (expanded, stop_iter)

def main():
  ## create index
  es = ES()
  if FLAGS_FIRST_RUN:
    if es.check_existing_index(index_name=FLAGS_CORPUS_NAME, delete_existing=False):
      es.create_skipgram2eid_index(index_name=FLAGS_CORPUS_NAME, type_name="skipgram2eid")
      es.create_eid2skipgram_index(index_name=FLAGS_CORPUS_NAME, type_name="eid2skipgram")
      es.create_eid2eid_index(index_name=FLAGS_CORPUS_NAME, type_name="eid2eid")


    start = time.time()
    skipgram2id, skipgram2eidcounts, eid2skipgramcounts = util.load_skipgram2eidcounts(eidSkipgramFilePath)
    end = time.time()
    print("[INFO] Loading data using time %s (seconds)" % (end-start))

    start = time.time()
    eid2eid_w_strength = util.calculateEidSimilarity(skipgram2eidcounts)
    end = time.time()
    print("[INFO] Calculating eid-eid similarity using time %s (seconds)" % (end - start))


    es.index_skipgram2eid(index_name=FLAGS_CORPUS_NAME, type_name="skipgram2eid", skipgram2id=skipgram2id,
                          skipgram2eidcounts=skipgram2eidcounts)

    es.index_eid2skipgram(index_name=FLAGS_CORPUS_NAME, type_name="eid2skipgram", eid2skipgramcounts=eid2skipgramcounts)
    es.index_eid2eid(index_name=FLAGS_CORPUS_NAME, type_name="eid2eid", eid2eid_w_strength=eid2eid_w_strength)

    es.match_all(index_name=FLAGS_CORPUS_NAME, type_name="skipgram2eid")
    es.match_all(index_name=FLAGS_CORPUS_NAME, type_name="eid2skipgram")
    es.match_all(index_name=FLAGS_CORPUS_NAME, type_name="eid2eid")

  eid2ename, ename2eid = util.loadEidToEntityMap(eidEnameFilePath)
  eid2types = util.loadEidToTypeMap(eidTypeFilePath, ename2eid=ename2eid)

  # userInput = ["NBA", "NCAA", "NFL"] # sports league, good performance
  userInput = ["BBC", "HBO", "CNN", "Fox", "Channel 4"] # TV Channel, good performance
  # userInput = ["Twitter", "Microsoft", "Lenovo", "Toyota", "Qualcomm"] # company, good performance
  # userInput = ["Toyota", "Hyundai", "Mazda", "Chrysler", "Ford"] # car company (top-30, avg.rank=10), good performance
  # userInput = ["Google", "Facebook", "Microsoft", "Amazon", "Twitter"] # high tech company, good performance
  #
  # userInput = ["United States", "China", "Japan", "germany", "England", "Russia", "India"] # country, using dist.sim
  # userInput = ["Illinois", "Texas", "California", "Ohio", "Maryland"] # state, using dist.sim



  seedEidsWithConfidence = [(ename2eid[ele.lower()], 0.0) for ele in userInput]
  negativeSeedEids = set()
  params = SetExpanParams(index_name=FLAGS_CORPUS_NAME, max_iter=10, ensemble_batch=10, num_of_top_skipgrams=150,
                          num_of_top_candidate_eids=50, feature_subset_size_ratio=0.8, average_rank=10,
                          skipgramDistLower=3, skipgramDistUpper=30, use_type=False)

  start = time.time()
  (expanded_eids, stop_iter) = setExpan(es, seedEidsWithConfidence, negativeSeedEids, eid2ename, eid2types, params, FLAGS_DEBUG=False)
  end = time.time()
  print("[INFO!!!] Finish SetExpan++ in %s seconds" % (end-start))
  for ele in expanded_eids:
    print(ele[0], eid2ename[ele[0]], ele[1])

  ### For testing purpose
  # seedEids = [ele[0] for ele in seedEidsWithConfidence ]
  # es.search_sgid_by_eid(index_name="wiki", type_name="skipgram2eid", topK=50, lower_bound=3, upper_bound=30, eid_list=seedEids, DEBUG=True)


if __name__ == '__main__':
  main()
