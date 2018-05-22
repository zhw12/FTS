'''
__author__: Hanwen Zha
__description__: Use python code to excute taxongen pipline,
__latest_updates__: 3/28/2018
__compatible__: Python3
'''

import argparse
import os
import re
import subprocess
import sys
import time
from shutil import copyfile
import logging

# it is run through python {}/TaxonGen/taxongen_pipeline.py {} in tasks.py
# root_dir = '/home/hanwen/disk/demov3'
root_dir = os.path.abspath('..')
sys.path.append('{}/webUI/'.format(root_dir))
from utils.utils import decode_filename

# write the system log to system log file
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='{}/TaxonGen/taxongen_pipeline_system.log'.format(root_dir),
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.WARNING)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


# self-defined log file
log_file = '{}/TaxonGen/taxongen_pipeline.log'.format(root_dir)


def main(filename):
    # print('query', type(query), query)
    # print('min_score', type(min_score), min_score)
    #
    query, min_score = decode_filename(filename)

    env = {
        'MODEL': 'models/{}'.format(filename),
        'RAW_TRAIN': '{}/data/query_docs/{}.txt'.format(root_dir, filename),
        'TEXT_TO_SEG': '{}/data/query_docs/{}.txt'.format(root_dir, filename),
        'MIN_SUP': '5'
    }
    print('{}\t{}'.format(query, min_score), file=open(log_file, 'a'))
    # print('Generating taxonomy for {} above threshold {} ...'.format(query.replace('_', ' '), min_score), file=open(log_file, 'a'))
    print('Generating taxonomy ...', file=open(log_file, 'a'))

    time.sleep(1)
    print('Phrase Mining...', file=open(log_file, 'a'))
    time.sleep(1)
    subprocess.call('cd {}/AutoPhrase; bash auto_phrase.sh'.format(root_dir), shell=True, env=env)
    print('Phrase Segmentation...', file=open(log_file, 'a'))
    time.sleep(1)
    subprocess.call('cd {}/AutoPhrase; bash phrasal_segmentation.sh'.format(root_dir), shell=True, env=env)
    #
    # execute wikiLinker in TaxonGen/wikiLinker.py.
    print('Running Wiki Linker...', file=open(log_file, 'a'))
    input_phrase_file = '{}/AutoPhrase/models/{}/AutoPhrase.txt'.format(root_dir, filename)
    output_phrase_file = '{}/TaxonGen/linked_results.wiki.pos.tsv'.format(root_dir)
    subprocess.call('python {}/TaxonGen/wikiLinker.py {} {}'.format(root_dir, input_phrase_file, output_phrase_file), shell=True)


    def rmTag_concat_autophrase(line, no_hypen=False, remove_noise=False):
        if remove_noise:
            line = re.sub(r'[^\x00-\x7F]+', ' ', line)
            ## add space before and after special characters
            line = re.sub(r"([.,!:?()])", r" \1 ", line)
            ## replace multiple continuous whitespace with a single one
            line = re.sub(r"\s{2,}", " ", line)

        def concat(matched):
            phrase = matched.group()
            phrase = re.sub('<phrase>', '', phrase)
            phrase = re.sub('</phrase>', '', phrase)
            if no_hypen:  # remove hypen in matched keywords
                phrase = re.sub('-', '_', phrase)
            return '_'.join(phrase.split())

        res = re.sub("<phrase>(.*?)</phrase>", concat, line)

        return res

    print('Preparing TaxonGen Data...', file=open(log_file, 'a'))
    # preprocessed segged output
    cnt = 0
    input_segged_file = '{}/AutoPhrase/models/{}/segmentation.txt'.format(root_dir, filename)
    output_segged_file = '{}/AutoPhrase/models/{}/segmentation_underscore.txt'.format(root_dir, filename)
    with open(input_segged_file, "r") as fin, open(output_segged_file, "w") as fout:
        for line in fin:
            cnt += 1
            if cnt % 10000 == 0:
                print(cnt)
            line = line.strip()
            line = line.lower()
            fout.write(rmTag_concat_autophrase(line, no_hypen=True, remove_noise=True))
            fout.write("\n")

    # prepare keywords for taxongen
    with open('{}/TaxonGen/linked_results.wiki.pos.tsv'.format(root_dir)) as fin:
        data = [i for i in fin]
        data = data[1:]
        phrase_cnt = 0
        phrase_list = []
        for d in data:
            phrase, combined_score, _ = d.split('\t', 2)
            score = float(combined_score)
            if score >= 1.0:
                phrase_list.append(phrase)
                phrase_cnt += 1

    print('#%d phrases' % phrase_cnt)
    print(phrase_list[:10], '...')

    with open('{}/TaxonGen/keywords.txt'.format(root_dir), 'w') as fout:
        for phrase in phrase_list:
            phrase = phrase.replace(' ', '_')
            fout.write(phrase + '\n')
    #
    local_embedding_data_dir = '{}/local-embedding/data/{}'.format(root_dir, filename)
    # #
    os.makedirs(local_embedding_data_dir, exist_ok=True)
    os.makedirs('{}/raw'.format(local_embedding_data_dir), exist_ok=True)
    os.makedirs('{}/input'.format(local_embedding_data_dir), exist_ok=True)

    copyfile('{}/TaxonGen/keywords.txt'.format(root_dir), '{}/raw/keywords.txt'.format(local_embedding_data_dir))
    copyfile('{}/AutoPhrase/models/{}/segmentation_underscore.txt'.format(root_dir, filename),
             '{}/raw/papers.txt'.format(local_embedding_data_dir))

    copyfile('{}/embedding/embeddings.txt'.format(root_dir), '{}/input/embeddings.txt'.format(local_embedding_data_dir))

    # prepare embedding for taxongen

    pd = dict()
    pd['data_dir'] = '{}/'.format(local_embedding_data_dir)
    pd['doc_file'] = pd['data_dir'] + 'input/papers.txt'
    pd['doc_keyword_cnt_file'] = pd['data_dir'] + 'input/keyword_cnt.txt'
    pd['input_dir'] = pd['data_dir'] + 'input/'
    pd['root_node_dir'] = pd['data_dir'] + 'cluster/'

    print('Running TaxonGen...', file=open(log_file, 'a'))
    subprocess.call('cd {}/local-embedding/code; bash run.sh'.format(root_dir), env={'corpusName': filename}, shell=True)


    print('Convert and Visualize TaxonGen Result...', file=open(log_file, 'a'))
    subprocess.call('python {}/TaxonGen/taxon2json.py {}'.format(root_dir, filename), shell=True)
    print('Finished.', file=open(log_file, 'a'))
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    query = args.query
    main(query)