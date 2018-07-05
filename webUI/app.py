'''
__author__ : Hanwen Zha
__description__: Main function starting Flask and run for NSCTA-Demo
__latest_update__: 5/2/2018
'''
import argparse
import json
import math
import os
import re
import time
import subprocess
import sys
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from luqum.parser import parser as luqum_parser
from luqum.elasticsearch import ElasticsearchQueryBuilder
import html

from flask import (Flask, json, jsonify, render_template, request)
from flask_cors import CORS, cross_origin
from flask import send_from_directory
from flask import redirect

from concept_based_retrieval import util as concept_util
from SetExpan import es, main, util
from attach_taxonomy.attach_taxonomy import attach_taxonomy
from celery_task.tasks import send_taxongen_task, load_taxongen_tasks, send_hiexpan_task
from utils.utils import is_single_query, encode_filename, decode_filename, clean_raw_query
from utils import treeNode

app = Flask(__name__, static_url_path='/static')
cors = CORS(app)
'''
use a local copy of luqum 0.6.0 
luqum/elasticsearch/tree.py is modified at line 58
add scoring_boolean to inner json
to adjust the scoring behavior of wildcard query
https://discuss.elastic.co/t/query-string-with-wildcard-does-not-calculate-score/5588/2

# luqum 0.7.0 is only compatible with ElasticSearch 6.x
# since match_phrase don't have zero_terms_query
'''

app = Flask(__name__)
app.config.from_envvar('APPLICATION_SETTINGS')

DEBUG_FLAG = app.config['DEBUG_FLAG']
es54 = es.ES()
eid2ename, ename2eid = util.loadEidToEntityMap("./data/wiki_entity2id.txt")
print("[INFO] finish loading entity2id")
eid2types = util.loadEidToTypeMap(
    './data/wiki_linked_results.txt', ename2eid=ename2eid)  # wiki_linked_results for SetExpan
print("[INFO] finish loading probase linking results")

with open('./webUI/static/id2path.json') as f:
    tid2path = json.load(f)
with open('./webUI/static/tree.json') as f:
    taxonomy = json.load(f)
print("[INFO] finish loading taxonomy files")

# extra files are watched by flask
# tree_g is the general taxonomy
# extra_files = ['./webUI/static/tree_g.json']

# part of luqum parser, generate ElasticSearch query from Lucene query
es_builder = ElasticsearchQueryBuilder(default_operator='must', default_field='text')

# root_dir = os.path.abspath('.')
root_dir = Path(__file__).absolute().parent.parent
ES_HOST = '127.0.0.1:9200'


def parse_tree(node, taxonID):
    # if node['taxonID'] == taxonID:
    #     return node
    if node.get('taxonID', 'xxx') == taxonID:
        return node
    elif 'children' in node:
        for child in node['children']:
            n = parse_tree(child, taxonID)
            if n:
                return n
    return


@app.route('/about')
def index():
    return render_template('index.html')


# @app.route('/video')
# def done():
#     return redirect('/static/fts-video.mov')

@app.route('/video')
def video():
    return render_template("video.html", filename='/static/fts-video.mp4')


@app.route('/v/<filename>')
def get_file(filename):
    return send_from_directory(root_dir / 'resources/', filename)


# This function is the d3.js tree interface
# parameters are in the tree.js file
# @app.route('/taxongen')
@app.route('/tree')
def tree():
    filename = request.args.get('filename', default='')
    if filename:
        try:
            with open(root_dir / 'HiExpan/data/dblp/results/{}/taxonomy_final.json'.format(filename)) as fin:
                tree_data = json.load(fin)
        except FileNotFoundError:
            with open(root_dir / 'webUI/static/tree.json') as fin:
                tree_data = json.load(fin)
    else:
        # default
        with open(root_dir / 'webUI/static/tree.json') as fin:
            tree_data = json.load(fin)
    h_json_out = {'corpus': 'DBLP', 'tree_data': tree_data}

    return render_template('tree.html', output_json=h_json_out)


# pie chart interface
@app.route('/pie', methods=['GET'])
@app.route('/pie/<taxonID>', methods=['GET', 'POST'])
def show_pie(taxonID=None):
    query = ''
    start_year = None
    end_year = None
    if request.method == 'POST':
        query = request.form['inputData']
        if len(query.split('-')) == 2:
            start_year, end_year = query.split('-')

    res = {}
    res['pieData'] = []

    node = parse_tree(taxonomy, taxonID)
    if node:
        children_list = node.get('children', [])
    else:
        children_list = []

    for child in children_list:
        childTaxonID = child['taxonID']
        name = child['name']

        res_json = search_api(query=None, taxonID=childTaxonID,
                              page=1, start_year=start_year, end_year=end_year)
        value = res_json['hits']['total']
        res['pieData'].append({
            "label": name,
            "value": value,
        })
    res['raw_query'] = query

    if taxonID and taxonID != '0_0_0':
        res['path'] = 'computer_science/' + tid2path[taxonID.split('_')[-1]]
        res['currentUrl'] = '/search/' + taxonID
        res['currentTaxonID'] = taxonID
    else:
        res['path'] = 'computer_science'
        res['currentUrl'] = '/search'
        res['currentTaxonID'] = '0_0_0'

    res['title'] = 'Subarea Shares of ' + \
                   res['path'].replace('_', ' ').title()

    res['titleFont'] = 24 if len(res['title']) < 40 else 20
    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)
    return render_template('pie.html', output_json=h_json_out)


def get_bar_data(country_list=None, query_list=None, taxonID=None, query=None):
    def get_cnt(data, year):
        for d in data:
            if d['key'] == year:
                return d['doc_count']
        return 0

    yearData = {}
    if query_list:
        for query in query_list:
            res = search_api(and_list=[query],
                             taxonID=taxonID, aggs=1, abstract=1, min_score=0)
            yearData[query] = res['aggregations']['years']['buckets']
    if country_list:
        for country in country_list:
            res = search_api(query=query, taxonID=taxonID,
                             aggs=1, abstract=1, country=country)
            yearData[country] = res['aggregations']['years']['buckets']

    res = {}
    res['barData'] = []
    start_year = 1993
    # start_year = 2005
    end_year = 2017
    res['barData'].append(
        ['year'] + list(range(start_year, end_year, 1))
    )

    total_res = search_api(query=None, taxonID=None,
                           aggs=1, abstract=1, country=None)
    totalYearData = total_res['aggregations']['years']['buckets']

    for v in yearData:
        data = [v]
        for y in range(start_year, end_year):
            data.append(get_cnt(yearData[v], y) /
                        float(get_cnt(totalYearData, y)))
            # data.append(get_cnt(yearData[v], y))
        res['barData'].append(data)

    if taxonID and taxonID != '0_0_0':
        res['path'] = 'computer_science/' + tid2path[taxonID.split('_')[-1]]
        res['currentUrl'] = '/search/' + taxonID
        res['currentTaxonID'] = taxonID
    else:
        res['path'] = 'computer_science'
        res['currentUrl'] = '/search'
        res['currentTaxonID'] = '0_0_0'

    if query_list:
        res['title'] = 'Shares of Different Topics in Research Area:'
        res['subtitle'] = res['path'].replace('_', ' ').title()
        res['placeholder'] = 'Type areas separated by , e.g. machine learning, data mining'

    if country_list:
        res['title'] = 'Shares of Different Countries in Research Area:'
        res['subtitle'] = res['path'].replace('_', ' ').title()
        res['placeholder'] = 'Type countries separated by , e.g. United States, China'

    res['titleFont'] = 20 if len(res['title']) < 80 else 16
    res['subtitleFont'] = 16 if len(res['subtitle']) < 80 else 12

    return res


@app.route('/bar', methods=['GET'])
@app.route('/bar/<taxonID>', methods=['GET', 'POST'])
def show_bar(taxonID=None):
    print('in show bar!')
    # query_list = []
    if request.method == 'POST':
        inputData = request.form['inputData']
        query_list = inputData.split(',')
    else:
        query_list = ['machine learning', 'data mining']
    res = get_bar_data(country_list=None,
                       query_list=query_list, taxonID=taxonID)
    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)
    return render_template('bar.html', output_json=h_json_out)


@app.route('/country_bar', methods=['GET'])
@app.route('/country_bar/<taxonID>', methods=['GET', 'POST'])
def show_country_bar(taxonID=None):
    # country_list = []
    if request.method == 'POST':
        inputData = request.form['inputData']
        country_list = inputData.split(',')
    else:
        country_list = ['United States', 'China']

    res = get_bar_data(country_list=country_list,
                       query_list=None, taxonID=taxonID)
    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)
    return render_template('bar.html', output_json=h_json_out)


# This function is used to test SetExpan
@app.route('/set_expan')
def set_expan():
    return render_template('setexpan_main.html')


@app.route('/set_expan_search', methods=['POST'])
def set_expan_search():
    params = main.SetExpanParams(index_name="wiki2", max_iter=10, ensemble_batch=20, num_of_top_skipgrams=150,
                                 num_of_top_candidate_eids=30, feature_subset_size_ratio=0.8, average_rank=5,
                                 skipgramDistLower=3, skipgramDistUpper=30, use_type=False, parallel_ensemble=True)

    query = request.form['inputData']
    if query == '':
        return render_template('setexpan_main.html')

    userInput = [str(ele.strip()) for ele in query.split(",")]
    all_in_candidates = True
    no_eid_candidates = []
    for ele in userInput:
        if ele.lower() not in ename2eid:
            all_in_candidates = False
            no_eid_candidates.append(ele)

    if not all_in_candidates:
        no_eid_cnt = len(no_eid_candidates)
        no_eid_query_string = ", ".join(no_eid_candidates)
        res = {
            "no_eid_cnt": no_eid_cnt,
            "no_eid_query_string": no_eid_query_string,
            "seed_entities": userInput
        }
        res_json = json.dumps(res, ensure_ascii=False)
        h_json_out = json.loads(res_json)
        return render_template('setexpan_noeid.html', results=res_json, output_json=h_json_out)

    print("[SetExpan] Seed set: %s" % userInput)
    seedEidsWithConfidence = [(ename2eid[ele.lower()], 0.0)
                              for ele in userInput]
    negativeSeedEids = set()

    start = time.time()
    (expanded_eids, stop_iter) = main.setExpan(es54, seedEidsWithConfidence, negativeSeedEids, eid2ename, eid2types,
                                               params,
                                               FLAGS_DEBUG=False)
    end = time.time()
    print("[INFO!!!] Finish SetExpan++ in %s seconds" % (end - start))

    res = {
        "query": query,
        "use_time": (end - start),
        "result_cnt": len(expanded_eids),
        "seed_cnt": len(userInput),
        "seed_entities": userInput,
        "expanded_eids": expanded_eids,
        "num_iteration:": stop_iter
    }

    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)
    return render_template('setexpan_results.html', results=res_json, output_json=h_json_out)


def scan_query_and_save(raw_query, query_body, min_score=0, save=True):
    es = Elasticsearch([ES_HOST])  # '127.0.0.1:9200'
    s = Search(using=es, index='taxongen1')
    s.update_from_dict(query_body)
    cnt = 0
    filename = encode_filename(raw_query, min_score)
    print('in scan_query_and_save', filename)

    if save:
        query_doc_directory = './data/query_docs'
        if not os.path.exists(query_doc_directory):
            os.makedirs(query_doc_directory)
        with open('{}/{}.txt'.format(query_doc_directory, filename), 'w') as f_out:
            for hit in s.scan():
                # print(hit.title)
                res = hit.title + ' ' + hit.paperAbstract
                res = res.replace('\n', ' ').replace('\r', '')
                # res = (res + '\n').encode('utf-8')
                res = res + '\n'  # Python3 write() argument must be str, not bytes
                f_out.write(res)
                cnt += 1


# Depreciated: Give a raw query and save the retrieved corpus
# @app.route('/analyze', methods=['GET'])
# def analyze():
#     raw_query = request.args.get('raw_query', default='')
#     min_score = request.args.get('min_score', default=0)
#
#     print('begin analyzing {} under minimum score {}...'.format(raw_query, min_score))
#
#     page = 1
#     enter = None
#     taxonID = None
#     and_list, or_list = query_parser(raw_query)
#     print(and_list, or_list)
#     # h_json_out = search_api(raw_query=raw_query,
#     #                         common_terms_query=raw_query, and_list=and_list, or_list=or_list, taxonID=taxonID,
#     #                         page=page, enter=enter,
#     #                         abstract=True, min_score=min_score, save=True)
#     h_json_out = search_api_lucene_syntax(raw_query, min_score=min_score, page=page, lucene_syntax=True, save=True)
#
#     return jsonify('success!')


@app.route('/generate_taxonomy', methods=['GET'])
def generate_taxonomy():
    raw_query = request.args.get('inputData', default='')
    raw_query = clean_raw_query(raw_query)
    min_score = request.args.get('min_score', default=0)
    min_score = int(min_score)
    if not raw_query:
        return jsonify('query is empty!')

    existing_queries = []
    for filename in os.listdir('./data/generated_taxonomy'):
        if filename.endswith('.json') and filename != 'tree.json':
            existing_raw_query, existing_min_score = decode_filename(filename[5:-5])
            existing_queries.append((existing_raw_query, existing_min_score))

    if (raw_query.lower(), min_score) in existing_queries:
        return jsonify('taxonomy exists!')

    try:
        with open('./TaxonGen/taxongen_pipeline.log') as fin:
            log_text = fin.read()
    except Exception:
        log_text = ''

    # override self-defined taxongen_pipeline.log after finished
    if re.search(pattern='Finished', string=log_text):
        with open('./TaxonGen/taxongen_pipeline.log', 'w') as fout:
            fout.write('')
    # elif re.search(pattern='Taxonomy Generation .+', string=log_text):
    #     text = re.findall(pattern='Taxonomy Generation .+', string=log_text)
    #     return jsonify(text[0])

    print('begin analyzing {} under minimum score {}...'.format(raw_query, min_score))

    page = 1

    h_json_out = search_api_lucene_syntax(raw_query, min_score=min_score, page=page, lucene_syntax=True, save=True)

    task_dict = load_taxongen_tasks('./TaxonGen/taxongen_task_list.txt')
    current_tasks = len(task_dict) + 1

    # check the task list before sending the task
    send_taxongen_task.apply_async(args=[raw_query, min_score], countdown=20 * (current_tasks - 1))
    return jsonify('taxonomy generation query submitted!')

def loadEidToEntityMap(filename):
    eid2ename = {}
    ename2eid = {}
    with open(filename, 'r') as fin:
        for line in fin:
            seg = line.strip('\r\n').split('\t')
            eid2ename[int(seg[1])] = seg[0]
            ename2eid[seg[0]] = int(seg[1])
    return eid2ename, ename2eid

@app.route('/hi_expan', methods=['GET', 'POST'])
def hi_expan():
    h_json_out = {}
    if request.method == 'POST':
        print(request)
        seed_taxonomy = request.form.get('inputData')
        seed_taxonomy = json.loads(seed_taxonomy)
        corpus = 'dblp'
        taxon_prefix = request.form.get('filename')

        # check input entity validation
        _, ename2eid = loadEidToEntityMap(root_dir/'HiExpan/data/{}/intermediate/entity2id.txt'.format(corpus))

        invalid_entities = []
        ename2eid['ROOT'] = 0
        for node in seed_taxonomy:
            for child in [node[0]] + node[2]:
                if child not in ename2eid:
                    invalid_entities.append(child)
        invalid_entities = list(set(invalid_entities))
        if invalid_entities:
            return jsonify("Concepts not in the system:", invalid_entities)

        seed_taxonomy = json.dumps(seed_taxonomy)

        send_hiexpan_task.apply_async(args=[corpus, taxon_prefix, seed_taxonomy], countdown=0)
        return jsonify("Taxonomy generation query submitted!")

    existing_taxonomies = []
    for dirname in os.listdir(root_dir / 'HiExpan/data/dblp/results'):
        existing_taxonomies.append(dirname)
    h_json_out['existing_taxonomies'] = existing_taxonomies

    return render_template('HiExpan.html', output_json=h_json_out)


# a simplified version of lucence syntax query
def search_api_lucene_syntax(raw_query, min_score=0, page=1, save=False, lucene_syntax=False):
    if not raw_query or not lucene_syntax:
        print('query should be lucene syntax and not be empty')
        raise Exception

    INDEX_NAME = 'taxongen1'
    TYPE_NAME = 'taxongen_docs'
    # ES_HOST = '127.0.0.1:9200'
    ES_PAGE_SIZE = 10

    FROM = (page - 1) * 10
    SIZE = ES_PAGE_SIZE

    query_body = {
        'min_score': min_score,
        'from': FROM,
        'size': SIZE,
    }
    luqum_tree = luqum_parser.parse(raw_query)  # '(title:"foo bar" AND body:"quick fox") OR title:fox'
    # luqum_tree = FieldGroupUnknownResolver(luqum_tree)
    # luqum_tree = NoAttributeUnknownResolver(luqum_tree)
    luqum_query = es_builder(luqum_tree)

    query_body['query'] = luqum_query

    if save:
        scan_query_and_save(raw_query, query_body, min_score)
        return
    es = Elasticsearch(hosts=[ES_HOST])

    start = time.time()
    res = es.search(
        index=INDEX_NAME,
        request_timeout=180,
        body=query_body
    )
    end = time.time()

    res['raw_query'] = raw_query
    res['query_time'] = (end - start)
    res['current_page'] = page
    visable_pages = int(math.ceil(float(res['hits']['total']) / ES_PAGE_SIZE))
    res['total_pages'] = visable_pages if visable_pages < 1000 else 1000

    # enable highlight only when single query
    res['highlight_term_list'] = []
    if is_single_query(raw_query):
        term = raw_query.replace('_', ' ')
        if term.endswith('es'):
            res['highlight_term_list'].append([term[:-2], 'a'])
        elif term.endswith('s'):
            res['highlight_term_list'].append([term[:-1], 'a'])
        res['highlight_term_list'].append([term, 'a'])

    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)

    return h_json_out


def search_api(query='', taxonID='', page=1, start_year=None, end_year=None, aggs=False, abstract=False, country='',
               match_phrase_query='', common_terms_query=None, and_list=[], or_list=[], enter=None, query_body=None,
               concept=None, min_score=0, raw_query='', save=False):
    '''
        First Version search api above elasticsearch query,
        Mainly work for pie/bar chat now,
        will be replaced by search_api_lucene_syntax
    '''

    if not query_body:
        if start_year and not end_year:
            end_year = 2016
        elif not start_year and end_year:
            start_year = 1991

        INDEX_NAME = 'taxongen1'
        TYPE_NAME = 'taxongen_docs'
        # ES_HOST = '127.0.0.1:9200'
        ES_PAGE_SIZE = 10

        if aggs:
            FROM = 0
            SIZE = 0
        else:
            FROM = (page - 1) * 10
            SIZE = ES_PAGE_SIZE

        es = Elasticsearch(hosts=[ES_HOST])

        query_body = {
            'min_score': min_score,
            'from': FROM,
            'size': SIZE,
            'query': {
                'bool': {
                    'must': [],
                    'should': []
                }
            }
        }

        if country:
            query_body['query']['bool']['must'].append(
                {
                    'match_phrase': {
                        'country': {
                            'query': country
                        }
                    }
                },
            )

        if query:
            if abstract:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'title': {
                                            'query': query,
                                            'boost': 16
                                        }
                                    },

                                },
                                {
                                    'match': {
                                        'paperAbstract': {
                                            'query': query,
                                            'boost': 3
                                        }
                                    },

                                },
                            ]

                        }
                    }
                )
            else:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'title': {
                                            'query': query
                                        }
                                    },
                                },
                            ]

                        }
                    }
                )
        if match_phrase_query:
            if abstract:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'match_phrase': {
                                        'title': {
                                            'query': match_phrase_query,
                                            'boost': 16
                                        }
                                    }
                                },
                                {
                                    'match_phrase': {
                                        'paperAbstract': {
                                            'query': match_phrase_query,
                                            'boost': 3
                                        }
                                    }
                                },
                            ]

                        }
                    }
                )
            else:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'match_phrase': {
                                        'title': match_phrase_query
                                    }
                                },
                            ]

                        }
                    }
                )
        # if common_terms_query:
        for common_terms_query in and_list:
            if abstract:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'common': {
                                        'title': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                                {
                                    'common': {
                                        'paperAbstract': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                            ]

                        }
                    }
                )
            else:
                query_body['query']['bool']['must'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'common': {
                                        'title': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                            ]

                        }
                    }
                )

        for common_terms_query in or_list:
            if abstract:
                query_body['query']['bool']['should'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'common': {
                                        'title': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                                {
                                    'common': {
                                        'paperAbstract': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                            ]

                        }
                    }
                )
            else:
                query_body['query']['bool']['should'].append(
                    {
                        'bool': {
                            'should': [
                                {
                                    'common': {
                                        'title': {
                                            'query': common_terms_query,
                                            'cutoff_frequency': 0.001,
                                        }
                                    },
                                },
                            ]

                        }
                    }
                )

        # Inital paper ranking under a node
        if enter:
            # query_body['query']['bool']['should'] = []
            if taxonID:
                node = parse_tree(taxonomy, taxonID)
            else:
                node = parse_tree(taxonomy, '0_0_0')
            rank = 1.0
            for keyword in node['keywords']:
                rank += 1
                keyword = keyword.replace('_', ' ')
                query_body['query']['bool']['should'].append(
                    {
                        'match_phrase': {
                            'title': {
                                'query': keyword,
                                'boost': 16 / rank
                            }
                        }
                    },
                )
                query_body['query']['bool']['should'].append(
                    {
                        'match_phrase': {
                            'paperAbstract': {
                                'query': keyword,
                                'boost': 3 / rank
                            }
                        }
                    },
                )

        if taxonID:
            taxonID = taxonID
            query_body['query']['bool']['must'].append(
                {
                    'match': {'taxonIDs': taxonID}
                }
            )

        if start_year and end_year:
            query_body['query']['bool']['must'].append(
                {
                    'range': {
                        'year': {
                            'gte': start_year,
                            'lte': end_year,
                            'format': 'yyyy||yyyy'
                        }
                    }
                }
            )

        if aggs:
            query_body['aggs'] = {
                'years': {
                    'terms': {
                        'field': 'year',
                        'size': 100  # a large enough number contain all year buckets
                    }
                }
            }

    if save:
        scan_query_and_save(raw_query, query_body)
        return

    start = time.time()
    res = es.search(
        index=INDEX_NAME,
        request_timeout=180,
        body=query_body
    )
    end = time.time()

    res['raw_query'] = query
    res['query_time'] = (end - start)
    res['current_page'] = page
    visable_pages = int(math.ceil(float(res['hits']['total']) / ES_PAGE_SIZE))
    res['total_pages'] = visable_pages if visable_pages < 1000 else 1000

    node = parse_tree(taxonomy, taxonID)
    if node:
        keywords = node['keywords']
    else:
        keywords = []

    res['highlight_term_list'] = []
    if enter:
        for keyword in keywords:
            term = keyword.replace('_', ' ')
            if term.endswith('es'):
                res['highlight_term_list'].append([term[:-2], 'a'])
            elif term.endswith('s'):
                res['highlight_term_list'].append([term[:-1], 'a'])
            res['highlight_term_list'].append([term, 'a'])
        if query:
            for term in query.split(' '):
                res['highlight_term_list'].append([term, 'a'])
    for query in and_list + or_list:
        res['highlight_term_list'].append([query, 'a'])
    if taxonID and taxonID != '0_0_0':
        res['path'] = 'computer_science/' + tid2path[taxonID.split('_')[-1]]
        res['currentTaxonID'] = taxonID
        res['currentUrl'] = '/search/' + taxonID
    else:
        res['path'] = 'computer_science'
        res['currentUrl'] = '/search'
        res['currentTaxonID'] = '0_0_0'

    res['enter'] = True
    res['isLastLevel'] = False
    if taxonID:
        if int(taxonID.split('_')[0]) == 3:  # max 3 level for dblp taxonomy
            res['isLastLevel'] = True

    res_json = json.dumps(res, ensure_ascii=False)
    h_json_out = json.loads(res_json)

    return h_json_out


'''
    Simple query parser by hand,
    only works for pie/bar,
    will be replaced by search_api_lucene_syntax in the future
'''


def query_parser(query):
    # res =  re.split(pattern='( AND | OR )', string=query)
    if 'AND' in query:
        res = re.split(pattern=' AND | OR ', string=query)
        and_list = [r for r in res if r]
        or_list = []
    elif 'OR' in query:
        res = re.split(pattern=' AND | OR ', string=query)
        and_list = []
        or_list = [r for r in res if r]
    else:
        and_list = [query] if query else []
        or_list = []
    return and_list, or_list


def get_match_paper_count(query_list, min_score=0, option='OR'):
    '''
    Function used in query expansion and taxonomy display,
    get the number of papers
    :param query_list: node['name'], raw_query
    :param min_score:
    :param option:
    :return:
    '''
    # if isinstance(query_list, str) or isinstance(query_list, unicode):
    if isinstance(query_list, str):
        raw_query = query_list
        result = search_api_lucene_syntax(raw_query, min_score=min_score, lucene_syntax=True)
    elif len(query_list) == 1:
        raw_query = query_list[0]
        result = search_api_lucene_syntax(raw_query, min_score=min_score, lucene_syntax=True)
    elif option == 'AND':
        raw_query = '({}) AND ({})'.format(query_list[0], query_list[1])
        result = search_api_lucene_syntax(raw_query, min_score=min_score, lucene_syntax=True)
    else:
        raw_query = '({}) OR ({})'.format(query_list[0], query_list[1])
        result = search_api_lucene_syntax(raw_query, min_score=min_score, lucene_syntax=True)

    return int(result['hits']['total'])


# def get_match_paper_count(query_list, min_score=0, option='OR'):
#     # if isinstance(query_list, str) or isinstance(query_list, unicode):
#     if isinstance(query_list, str):
#         result = search_api(and_list=[query_list], abstract=True, min_score=min_score)
#     elif option == 'AND':
#         result = search_api(and_list=query_list, abstract=True, min_score=min_score)
#     else:
#         result = search_api(or_list=query_list, abstract=True, min_score=min_score)
#
#     return int(result['hits']['total'])


@app.route('/paper_count_get', methods=['GET'])
def get_match_paper_count_view():
    '''
    HTML GET function for js ajax get to get paper count
    :return:
    '''
    raw_query = request.args.get('raw_query', default='')
    min_score = request.args.get('min_score', default=0)
    new_query = request.args.get('new_query', default='')

    # in tree.js stored with - ?
    raw_query = raw_query.replace('_', ' ')
    new_query = new_query.replace('_', ' ')

    # result = search_api(and_list=[raw_query, new_query], abstract=True, min_score=min_score)
    raw_query = '({}) AND ({})'.format(raw_query, new_query)
    result = search_api_lucene_syntax(raw_query, min_score=min_score)
    result = int(result['hits']['total'])
    return jsonify(result)


def expand_query(query, candidate_size=40, min_score=0, min_expand_ratio=1.01):
    '''
    Query expansion function, expand by word2vec embedding similarity
    Exclude phrases with nearly the same information e.g. machine learning algorithm vs machine learning
    There is an issue with recurrent neural network vs neural network
    :param query:
    :param candidate_size:
    :param min_score:
    :param min_expand_ratio:
    :return:
    '''
    keyword = concept_util.wrap_marker(query)
    if keyword in concept_util.model_concepts.wv.vocab:
        neigh_pairs = concept_util.model_concepts.most_similar(keyword, topn=candidate_size)
        # print('query', neigh_pairs)
        new_neigh_pairs = []
        nn_out = []
        for v in neigh_pairs:
            neigh_phrase = concept_util.displayString(v[0])
            if concept_util.is_phrase(v[0]) and neigh_phrase not in nn_out:
                nn_out.append(neigh_phrase)
                new_neigh_pairs.append(v)

        neigh_pairs = new_neigh_pairs[:]

        nn_out = []
        query_count = get_match_paper_count([query], min_score)
        nn_score = []
        for i, v in enumerate(neigh_pairs):
            neigh_phrase = concept_util.displayString(v[0])
            neigh_count = get_match_paper_count(neigh_phrase, min_score)
            expand_count = get_match_paper_count([query, neigh_phrase], min_score)
            expand_ratio = expand_count / (query_count + 1e-6)
            if expand_ratio < min_expand_ratio:
                continue

            nn_out.append(neigh_phrase +
                          ' %d' % neigh_count +
                          ' %.2f' % expand_ratio
                          )
            nn_score.append([neigh_phrase, v[0], expand_ratio, i])
    else:
        nn_out = []
    return nn_out


# view function for search page
# return main search result page -> search_results_jinja.html

@app.route('/search', methods=['POST'])
@app.route('/search/<taxonID>', methods=['POST', 'GET'])
def search(taxonID=None):
    if request.method == 'POST':
        query = request.form.get('inputData') or request.form.get('concept')
        min_score = request.form.get('min_score', default=0)
        query = clean_raw_query(query)

        if query:
            # query from the expansion button
            # format is deep learning 1100 1.25
            if re.search('[\.\d]+', query):
                # query = re.findall(pattern='[\w ]+(?=)', string=query)[0].strip()
                query = query.rsplit(' ', 2)[0]
        if 'pageSelect' in request.form:
            page = int(request.form['pageSelect'])
        else:
            page = 1

        try:
            min_score = float(min_score)
        except ValueError:
            min_score = 0
    else:
        query = ''
        page = 1
        min_score = 0
    enter = None
    if not query:
        enter = True

    print('min_score', min_score, 'query', query)

    # and_list, or_list = query_parser(query)
    # h_json_out = search_api(query=query,
    #     common_terms_query=query, and_list=and_list, or_list=or_list, taxonID=taxonID, page=page, enter=enter,
    #     abstract=True, min_score=min_score, lucene_syntax=True)

    h_json_out = search_api_lucene_syntax(query, min_score=min_score, page=page, lucene_syntax=True)

    h_json_out['raw_query'] = query
    h_json_out['min_score'] = min_score

    # if and_list:
    #     query = and_list[0]
    # elif or_list:
    #     query = or_list[0]

    h_json_out['concepts'] = expand_query(query, min_score=min_score) if query else []

    h_json_out['hits_paper'] = []
    h_json_out['hits_score'] = []
    h_json_out['flip_taxonomy'] = 0
    # score_list = [0, 5, 10]

    score_list = []
    # if min_score not in score_list:
    #     score_list.append(min_score)
    #     score_list = sorted(score_list)
    # for score in score_list:
    #     temp_h_json_out = search_api(
    #         common_terms_query=query, and_list=and_list, or_list=or_list, taxonID=taxonID, page=page, enter=enter,
    #         abstract=True, min_score=score)
    #     h_json_out['hits_paper'].append(temp_h_json_out['hits']['total'])
    #     h_json_out['hits_score'].append(score)

    h_json_out['hits_paper'].append(h_json_out['hits']['total'])
    h_json_out['hits_score'].append(min_score)

    return render_template('search_results_jinja.html', output_json=h_json_out)


# Depreciated: api for phrase suggestion
# @app.route('/api/phrase/<query>', methods=['GET', 'POST'])
# @cross_origin()
# def phrase_api(query):
#     INDEX_NAME = 'phrase1'
#     TYPE_NAME = 'phrase'
#     ES_HOST = '127.0.0.1:9200'
#     topK = 10
#     es = Elasticsearch(hosts=[ES_HOST])
#
#     suggDoc = {
#         "suggest": {
#             'prefix': query,
#             "completion": {
#                 "field": 'phrase',
#                 "size": topK
#             }
#         },
#     }
#     res = es.suggest(body=suggDoc, index=INDEX_NAME, request_timeout=180)
#     return jsonify(res)


# api for phrase suggestion
@app.route('/api/phrase', methods=['GET'])
@cross_origin()
def phrase_api():
    query = request.args.get('q', default=' ')
    INDEX_NAME = 'phrase1'
    TYPE_NAME = 'phrase'
    # ES_HOST = '127.0.0.1:9200'
    topK = 10
    es = Elasticsearch(hosts=[ES_HOST])

    suggDoc = {
        "suggest": {
            'prefix': query,
            "completion": {
                "field": 'phrase',
                "size": topK
            }
        },
    }

    # res = es.search(suggest_field='phrase',suggest_size=topK, suggest_text=query, index=INDEX_NAME, request_timeout=180)
    res = es.suggest(body=suggDoc, index=INDEX_NAME, request_timeout=180)
    return jsonify(res)


@app.route('/')
@app.route('/concept')
@app.route('/search', methods=['GET'])
def concept():
    return render_template('concept.html')


# taxonomy save is temporarily disabled
@app.route('/taxonomy_save', methods=['POST'])
def taxononmy_save():
    # import  ipdb; ipdb.set_trace();
    json_data = request.json
    raw_query = json_data['raw_query']
    data = json_data['tree'][0]

    # def clean_tree(node):
    #     if 'children' in node:
    #         if not node['children']:
    #             del node['children']
    #         else:
    #             for child in node['children']:
    #                 clean_tree(child)
    #     return
    #
    # try:
    #     clean_tree(data)
    # except Exception, e:
    #   import ipdb; ipdb.set_trace();
    #   raise e

    # if raw_query in ['quantum learning', 'quantum cryptography', 'quantum sensing']:
    #     with open('./webUI/static/tree_{}.json'.format(raw_query.replace(' ', '_')), 'w') as f_out:
    #         json.dump(data, f_out)
    # else:
    #     with open('./webUI/static/tree.json', 'w') as f_out:
    #         json.dump(data, f_out)
    return jsonify('success!')
    # return jsonify('Save  function is temporarily disabled')
    # return jsonify(data)


def get_tree_counts(node, raw_query='', min_score=0):
    '''
    Write count in the tree json
    :param node:
    :param raw_query:
    :param min_score:
    :return:
    '''
    raw_query = raw_query.replace('_', ' ')
    try:
        node['name'] = node['name'].replace('_', ' ')
    except Exception as e:
        return
    if raw_query:
        and_list = [node['name'], raw_query]
    else:
        and_list = [node['name']]

    # node['count'] = get_match_paper_count(and_list, min_score=min_score, option='AND')
    node['count'] = get_match_paper_count(and_list, min_score=min_score, option='AND')

    if 'children' in node:
        for child in node['children']:
            get_tree_counts(child, raw_query, min_score)


def expand_tree(node, level=0, max_level=1):
    if level <= max_level:
        node['open'] = True
        if 'children' in node:
            for child in node['children']:
                expand_tree(child, level + 1, max_level)


def expand_tree_by_name(node, name):
    # import pdb; pdb.set_trace();
    if node['name'].replace('_', ' ') == name.replace('_', ' '):
        return True
    if 'children' in node:
        flag = False
        for child in node['children']:
            flag = expand_tree_by_name(child, name)
            if flag:
                node['open'] = True
        if flag:
            return True
    return False


def exist_in_tree_by_name(node, name):
    if node['name'].replace('_', ' ') == name.replace('_', ' '):
        return True
    if 'children' in node:
        for child in node['children']:
            n = exist_in_tree_by_name(child, name)
            if n:
                return True
    return False


def parse_tree_by_name(node, name):
    '''
    Return a tree node by searching its name
    :param node:
    :param name:
    :return:
    '''
    if node['name'] == name:
        return node
    if 'children' in node:
        for child in node['children']:
            n = parse_tree_by_name(child, name)
            if n:
                return n
    return


def attach_tree_by_name(node, name, attach_dict):
    '''
    Attach queries to the tree
    :param node:
    :param name:
    :param attach_dict:
    :return:
    '''
    if node['name'].replace(' ', '_') in attach_dict:
        # import pdb; pdb.set_trace()
        if node.get('children', []):
            node['children'].append(
                {'name': name.replace('_', ' '), 'count': attach_dict[node['name'].replace(' ', '_')]})
        else:
            node['children'] = [{'name': name.replace('_', ' '), 'count': attach_dict[node['name'].replace(' ', '_')]}]
            return
    if 'children' in node:
        for child in node['children']:
            attach_tree_by_name(child, name, attach_dict)
    return


def get_tree_counts_init(node, raw_query):
    '''
    Hide tree counts by using ''
    :param node:
    :param raw_query:
    :return:
    '''
    raw_query = raw_query.replace('_', ' ')
    if raw_query != node['name'].replace('_', ' '):
        node['count'] = ''
    if 'children' in node:
        for child in node['children']:
            get_tree_counts_init(child, raw_query)


@app.route('/taxonomy_get', methods=['GET'])
def taxononmy_get():
    raw_query = request.args.get('raw_query', default='')
    min_score = request.args.get('min_score', default=0)
    flip_taxonomy = request.args.get('flip_taxonomy', default=0)
    min_score = int(min_score)
    flip_taxonomy = int(flip_taxonomy)
    raw_query = clean_raw_query(raw_query)
    # taxonomy_path = './webUI/static/tree_{}.json'.format(raw_query.replace(' ', '_'))
    # taxonomy_path = './data/generated_taxonomy/tree_{}.json'.format(raw_query.replace(' ', '_'))
    taxonomy_path = './data/generated_taxonomy/tree_{}.json'.format(encode_filename(raw_query, min_score))
    # if os.path.exists(taxonomy_path):
    #     with open(taxonomy_path) as f_in:
    #         data = json.load(f_in)
    # else:

    # general taxonomy
    # with open('./webUI/static/tree.json') as f_in:
    #     data = json.load(f_in)
    with open('./data/generated_taxonomy/tree.json') as f_in:
        data = json.load(f_in)

    # if isinstance(data, list):
    #     get_tree_counts(data[0], raw_query, min_score)
    #     expand_tree(data[0])
    # else:
    #     get_tree_counts(data, raw_query, min_score)
    #     expand_tree(data)

    # guarantee it is a json dictionary (which has a root)
    if isinstance(data, list):
        data = data[0]

    # print('flip_taxonomy is', type(flip_taxonomy), flip_taxonomy)
    if flip_taxonomy:
        # in specific taxonomy
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path) as f_in:
                found_data = json.load(f_in)
        else:
            # specific taxonomy not exists, just find the node
            found_data = parse_tree_by_name(data, raw_query)

        if found_data:
            data = found_data
        expand_tree(data)
        get_tree_counts(data, raw_query, min_score)
    else:
        # attach taxonomy only when raw_query is single query
        if is_single_query(raw_query):
            expand_tree_by_name(data, raw_query)
            if exist_in_tree_by_name(data, raw_query):
                # get_tree_counts(data, raw_query, min_score)
                # get_tree_counts_init(data, raw_query)
                pass
            else:
                print('not found node!')
                top_phrases = attach_taxonomy(query=raw_query.replace(' ', '_'), model=concept_util.model_concepts)
                print(top_phrases)
                # import pdb; pdb.set_trace();
                # attach_tree_by_name(data, raw_query.replace(' ', '_'), [p for p in top_phrases])
                attach_tree_by_name(data, raw_query.replace(' ', '_'), top_phrases)
                expand_tree_by_name(data, raw_query)
                # get_tree_counts_init(data, raw_query)
                # get_tree_counts(data, raw_query, min_score)
        # else:
        # get_tree_counts(data, raw_query, min_score)
        get_tree_counts_init(data, raw_query)
        # pass

    # get_tree_counts(data, raw_query, min_score)
    return jsonify(data)


@app.route('/trend', methods=['POST', 'GET'])
def trend(taxonID=None):
    if request.method == 'POST':
        query = request.form.get('inputData') or request.form.get('concept')
        if query:
            if re.search('[\.\d]+', query):
                # query = re.findall(pattern='[\w ]+(?=)', string=query)[0].strip()
                query = query.rsplit(' ', 2)[0]
        if 'pageSelect' in request.form:
            page = int(request.form['pageSelect'])
        else:
            page = 1
        min_score = request.form.get('min_score', default=0)
        try:
            min_score = float(min_score)
        except ValueError:
            min_score = 0
    else:
        query = ''
        page = 1
        min_score = 0
    enter = None
    if not query:
        enter = True

    print('min_score', min_score, 'query', query)

    and_list, or_list = query_parser(query)
    h_json_out = search_api(
        common_terms_query=query, and_list=and_list, or_list=or_list, taxonID=taxonID, page=page, enter=enter,
        abstract=True, min_score=min_score)

    h_json_out['raw_query'] = query
    h_json_out['min_score'] = min_score

    if and_list:
        query = and_list[0]
    elif or_list:
        query = or_list[0]

    h_json_out['concepts'] = expand_query(query, min_score=min_score) if query else []

    h_json_out['hits_paper'] = []
    h_json_out['hits_score'] = []
    # score_list = [0, 5, 10]
    score_list = []
    if min_score not in score_list:
        score_list.append(min_score)
        score_list = sorted(score_list)
    for score in score_list:
        temp_h_json_out = search_api(
            common_terms_query=query, and_list=and_list, or_list=or_list, taxonID=taxonID, page=page, enter=enter,
            abstract=True, min_score=score)
        h_json_out['hits_paper'].append(temp_h_json_out['hits']['total'])
        h_json_out['hits_score'].append(score)

    return render_template('trend.html', output_json=h_json_out)


@app.route('/generate_taxonomy_view', methods=['POST', 'GET'])
def generate_taxonomy_view():
    h_json_out = {}
    existing_queries = []

    for filename in os.listdir('./data/generated_taxonomy'):
        if filename.endswith('.json') and filename != 'tree.json':
            # query = filename[5:-5].replace('_', ' ')  # tree_
            try:
                raw_query, min_score = decode_filename(filename[5:-5])
                existing_queries.append((raw_query, min_score))
            except:
                pass
    print('existing_queries', existing_queries)
    h_json_out['existing_queries'] = existing_queries

    try:
        with open('./TaxonGen/taxongen_pipeline.log') as fin:
            log_text = fin.read()
    except Exception:
        log_text = ''
    else:
        texts = log_text.strip().split('\n')
        if len(texts) >= 2:
            # raw_query = re.findall('(?<=Generating taxonomy for).+(?=\.\.\.)', texts[0])[0].strip()
            raw_query, min_score = texts[0].split('\t', 1)
            raw_query = raw_query.replace('_', ' ')
            min_score = int(min_score)
            h_json_out['raw_query'] = raw_query
            h_json_out['min_score'] = min_score
            h_json_out['log_title'] = texts[1]
        if len(texts) >= 3:
            h_json_out['log_texts'] = ['query: {}'.format(raw_query), 'threshold: {}'.format(min_score)]
            h_json_out['log_texts'].extend(texts[2:])

    return render_template('generate_taxonomy.html', output_json=h_json_out)


@app.route('/query_converter', methods=['GET', 'POST'])
def query_converter():
    h_json_out = {}
    if request.method == 'POST':
        raw_query = request.form.get('inputData')
        luqum_tree = luqum_parser.parse(raw_query)  # '(title:"foo bar" AND body:"quick fox") OR title:fox'
        luqum_query = es_builder(luqum_tree)

        h_json_out['luqum_query'] = json.dumps(luqum_query, indent=2)
        print(h_json_out['luqum_query'])

    return render_template('query_converter.html', output_json=h_json_out)


@app.route('/cancel_taxonomy_generation', methods=['GET'])
def cancel_taxonomy_generation():
    env = {
        'root_dir': root_dir,
    }
    raw_query = request.args.get('raw_query', default='')
    min_score = request.args.get('min_score', default=0)
    min_score = int(int(min_score))
    if raw_query:
        filename = encode_filename(raw_query, min_score)

        subprocess.call('bash ./TaxonGen/terminate_pipeline.sh', shell=True)
        subprocess.call('bash ./TaxonGen/clean.sh {}'.format(filename), shell=True, env=env)
    return jsonify('Task canceled.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='app.py',
                                     description='Main function of NSCTA-demo.')
    parser.add_argument('-port', required=False,
                        default=5002, help='Port number')
    parser.add_argument('-debug', required=False,
                        default=True, help='Port number')
    args = parser.parse_args()
    # print(os.path.isfile(extra_files[0]))
    # app.run(host='0.0.0.0', port=int(args.port),
    #         debug=True, threaded=True, extra_files=extra_files, use_reloader=True)  # for server
    app.run(host='0.0.0.0', port=int(args.port),
            debug=True, threaded=True, use_reloader=True)  # for server
