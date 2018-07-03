import re
import base64
import json
import hashlib
from pathlib import Path

from filelock import Timeout, FileLock
import os
import html


# path is inherited from its parent, (which is )
# root_dir = os.path.abspath('.') # /home/hanwen/disk/demov3
root_dir = Path(__file__).absolute().parent.parent.parent
# for normal use
dictionary_file = '{}/TaxonGen/filename2query.txt'.format(root_dir)
dictionary_lock_file = "{}/TaxonGen/filename2query.txt.lock".format(root_dir)

def is_single_query(raw_query):
    '''
        Helper function to judge whether a query is simple query or not
    '''
    if re.search('[\'"()]', raw_query):
        return False
    if 'AND' in raw_query or 'OR' in raw_query:
        return False
    return True

def get_decoder_from_file(dictionary_file):
    '''
        Store a local file for get raw query from hash code
    '''
    filename2query = {}
    try:
        with open(dictionary_file) as fin:
            for line in fin:
                fn, qry = line.strip().split('\t', 1)
                filename2query[fn] = qry
    except Exception as e:
        print('Exception', e, dictionary_file, 'Not found!')
        with open(dictionary_file, 'w') as fout:
            pass
    return filename2query


def encode_filename(raw_query, min_score=0, dictionary_file=dictionary_file, dictionary_lock_file=dictionary_lock_file):
    '''
        Use hashlib.md5 to hash, python3 hash has some randomness
        encode raw query only to a hash string, keep the dictionary_file clean
    '''
    if is_single_query(raw_query):
        filename = raw_query.replace(' ', '_')
        if min_score > 0:
            filename = filename + '_' + str(min_score)
    else:
        lock = FileLock(dictionary_lock_file, timeout=1)
        md5 = hashlib.md5(raw_query.encode())
        filename = md5.hexdigest() + '_{}_ishash'.format(min_score)
        print(raw_query, type(raw_query))
        print(min_score, type(min_score))
        print('encode_filename', filename)
        with lock:
            filename2query = get_decoder_from_file(dictionary_file)
            print('filename2query', filename2query)
            print('md5.hexdigest()', type(md5.hexdigest()), md5.hexdigest())
        with lock:
            if md5.hexdigest() not in filename2query:
                with open(dictionary_file, 'a') as fout:
                    fout.write(md5.hexdigest() + '\t' + raw_query + '\n')
    return filename


def decode_filename(filename, dictionary_file=dictionary_file):
    '''
        decode raw query and min score from filename
    '''
    if filename.endswith('_ishash'):
        filename = filename[:-7]
        filename2query = get_decoder_from_file(dictionary_file)
        hashcode, min_score = filename.rsplit('_', 1)
        min_score = int(min_score)
        raw_query = filename2query[hashcode]
    elif re.search('_[\d\.]+$', filename):
        raw_query, min_score = filename.rsplit('_', 1)
        raw_query = raw_query.replace('_', ' ')
        min_score = int(min_score)
    else:
        raw_query = filename.replace('_', ' ')
        min_score = 0
    return raw_query, min_score

def clean_raw_query(raw_query):
    '''
    Clean raw qurey: remove unnecessary space from raw query,
    unescape raw query from jinja html template (e.g. html converts "" to html marks)
    :param raw_query: raw query
    :return: cleaned raw query
    '''
    raw_query = raw_query.strip()
    raw_query = html.unescape(raw_query)
    raw_query = re.sub('\s+', ' ', raw_query)
    raw_query = raw_query.strip()
    return raw_query