'''
__author__: Jiaming Shen
__description__: A bunch of utility functions for elasticsearch based SetExpan
__latest_update__: 10/15/2017
'''
from collections import defaultdict
import itertools

def load_skipgram2eidcounts(filename):
  print("[INFO] Start loading data")
  cur_sg_id = 0
  skipgram2id = {}
  skipgram2eidcounts = defaultdict(list)
  eid2skipgramcounts = defaultdict(list)
  with open(filename, "r") as fin:
    for line in fin:
      line = line.strip()
      segs = line.split("\t")
      if len(segs) < 3:
        continue
      eid = segs[0] # string
      skipgram = segs[1]
      count = int(segs[2])
      if skipgram not in skipgram2id:
        skipgram2id[skipgram] = cur_sg_id
        cur_sg_id += 1

      sg_id = skipgram2id[skipgram]
      skipgram2eidcounts[skipgram].append((eid, count))
      eid2skipgramcounts[eid].append((sg_id, count))

  print("[INFO] Number of distinct skipgrams = %s" % cur_sg_id)
  return skipgram2id, skipgram2eidcounts, eid2skipgramcounts

def loadEidToEntityMap(filename):
  eid2ename = {}
  ename2eid = {}
  with open(filename, 'r') as fin:
    for line in fin:
      seg = line.strip('\r\n').split('\t')
      eid2ename[int(seg[1])] = seg[0]
      ename2eid[seg[0].lower()] = int(seg[1])
  return eid2ename, ename2eid

def loadEidToTypeMap(filename, ename2eid):
  eid2types = {} # eid -> {type:strength}
  with open(filename, "r") as fin:
    for line in fin:
      line = line.strip()
      segs = line.split("\t")
      eid = ename2eid[segs[0].lower()]
      if segs[1]:
        type_w_strength = eval(segs[1])
        type2strength = {ele[0]:ele[1] for ele in type_w_strength}
        eid2types[eid] = type2strength
      else:
        eid2types[eid] = {}

  return eid2types

def calculateEidSimilarity(skipgram2eidcounts):
  eid2eid_w_strength = defaultdict(lambda : defaultdict(int))
  greedy_sg_cnt = 0
  cnt = 0
  for eidcounts in skipgram2eidcounts.values():
    cnt += 1
    if (cnt % 100000 == 0):
      print("Processed %s skipgrams" % cnt)
    if len(eidcounts) > 200:
      greedy_sg_cnt += 1
      continue
    eids = [int(ele[0]) for ele in eidcounts]
    for eidpair in itertools.combinations(eids,2):
      eid2eid_w_strength[eidpair[0]][eidpair[1]] += 1
      eid2eid_w_strength[eidpair[1]][eidpair[0]] += 1

  print("Number of eid with context eid = %s" % len(eid2eid_w_strength))
  avg_context_eid = sum([len(ele) for ele in eid2eid_w_strength.values()]) / len(eid2eid_w_strength)
  print("Average number of context eid for each eid = %s" % avg_context_eid)
  print("Greedy skipgram count = %s " % greedy_sg_cnt)
  return eid2eid_w_strength

