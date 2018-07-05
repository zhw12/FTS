# tasks.py
import subprocess
import sys
import time
import os
from pathlib import Path

from celery import Celery

# celery path is webUI

# root_dir = '/home/hanwen/disk/demov3'
root_dir = os.path.abspath('..')
# root_dir = Path(__file__).absolute().parent.parent
sys.path.append('{}/TaxonGen/'.format(root_dir))
sys.path.append('{}/webUI/'.format(root_dir))

from utils.utils import encode_filename

from filelock import FileLock

celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')

dictionary_file = '{}/TaxonGen/filename2query.txt'.format(root_dir)
dictionary_lock_file = "{}/TaxonGen/filename2query.txt.lock".format(root_dir)

def load_taxongen_tasks(infile):
    task_dict = {}
    try:
        with open(infile) as fin:
            for line in fin:
                print(line)
                raw_query_, taskid_ = line.strip().split('\t')
                task_dict[raw_query_] = taskid_
    except FileNotFoundError:
        pass
    return task_dict


@celery.task
def send_taxongen_task(raw_query, min_score):
    print('task id is {}'.format(send_taxongen_task.request.id))
    print('entering {} with min_score...'.format(raw_query, min_score))
    lock_path = "{}/TaxonGen/taxongen_task_list.txt.lock".format(root_dir)
    lock = FileLock(lock_path, timeout=1)

    with lock:
        task_dict = load_taxongen_tasks('{}/TaxonGen/taxongen_task_list.txt'.format(root_dir))
    if raw_query in task_dict:
        return
    with lock:
        with open('{}/TaxonGen/taxongen_task_list.txt'.format(root_dir), 'a') as fout:
            fout.write(raw_query + '\t' + str(send_taxongen_task.request.id) + '\n')
    print('start taxongen pipeline of {}...'.format(raw_query))
    # time.sleep(5)
    # base64_query = base64.b64encode(raw_query.encode()).decode()
    # print('base64_query', type(base64_query), base64_query)

    # encode_filename for special use in tasks.py
    # dictionary_file and lock file need to be assigned
    filename = encode_filename(raw_query, min_score, dictionary_file, dictionary_lock_file)
    print('filename', filename)
    process = subprocess.Popen('python {}/TaxonGen/taxongen_pipeline.py {}'. format(root_dir, filename), shell=True)
    # taxongen_pipeline(raw_query)
    print('process.pid', process)
    print('finished')
    with lock:
        task_dict = load_taxongen_tasks('{}/TaxonGen/taxongen_task_list.txt'.format(root_dir))
        del task_dict[raw_query]
        with open('{}/TaxonGen/taxongen_task_list.txt'.format(root_dir), 'w') as fout:
            for raw_query, taskid in task_dict.items():
                fout.write(raw_query + '\t' + str(taskid) + '\n')

@celery.task
def send_hiexpan_task(corpus, taxon_prefix, seed_taxonomy):
    print('task id is {}'.format(send_hiexpan_task.request.id))
    print('corpus is {}'.format(corpus))
    print('seed taxonomy is {}'.format(seed_taxonomy))
    print('command is {}'.format('python {}/HiExpan/src/HiExpan-new/main.py '
                                 '-data {} -taxonPrefix test -user-input {}'. format(root_dir, corpus, seed_taxonomy)))
    process = subprocess.Popen('cd {}/HiExpan/src/HiExpan-new/; python main.py '
                               '-data {} -taxonPrefix {} -user-input \'{}\''. format(root_dir, corpus, taxon_prefix, seed_taxonomy), shell=True)
    print('process.pid', process)
    print('finished')


# @periodic_task(run_every=1)
# def some_task():
#     print('periodic task test!!!!!')