# FTS
The source code used for the demo FTS: Faceted Taxonomy Construction and Search for Scientific Publications, published in KDD 2018.

FTS is a network-based, unified search and navigation platform,
to ease query development and facilitate intelligence exploration
in a large text repository, focused on scientific publications.

Online Demo Url: <http://fts.cs.ucsb.edu/>

## Getting Started
This is an instruction for offline deployment of the
FTS System. The instruction is based on Ubuntu 16.04 LTS.

### Requirements
```
Python3, Python2, java, gcc, Elasticsearch, Redis
python libraries: elasticsearch, redis, celery, gensim, spacy, etc.
listed in webUI/requirements.txt(python3)
webUI/requirements_python2.txt(python2)
```

#### Python requirements
```
In root folder, Create the virtual environments venv, venv_py2

virtualenv --python=/usr/bin/python2 venv_py2
virtualenv --python=/usr/bin/python3 venv

Install requirements for python3:
source venv/bin/activate
(venv)$ pip install -r webUI/requirements.txt

Install requirements for python2 (used for taxongen):
source venv_py2/bin/activate
(venv_py2)$ pip install -r webUI/requirements_python2.txt
```

#### Elasticsearch
Use elasticsearch to index and search data
```
Install elasticsearch-5.4.1
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.4.1.tar.gz
tar -xvf elasticsearch-5.4.1.tar.gz
cd elasticsearch-5.4.1

Start elasticsearch
bin/elasticsearch -d
```

#### Redis
Use redis to store long time background job, e.g. taxonomy generation
```
Install redis
sudo apt-get install redis-server

Start reids
redis-server
```

#### Celery
Use celery to manage long time background job, e.g. taxonomy generation
```
source venv/bin/activate
(venv)$ pip install celery==4.1.0
(venv)$ pip install kombu==4.1.0
(venv)$ pip install billiard==3.5.0.2
```



#### Spacy
Use spacy to do text processing
```
Install spacy in python3
Enter python3 virtual environment, source venv/bin/activate
(venv)$ pip install spacy
Download spacy model file
(venv)$ python -m spacy download en
```
Spacy Installment Trouble Shooting: <https://spacy.io/usage/#section-troubleshooting>

<!--
Error: setup script exited with error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
Reference: https://stackoverflow.com/questions/26053982/setup-script-exited-with-error-command-x86-64-linux-gnu-gcc-failed-with-exit
Solution: sudo apt-get install libpq-dev python-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev


Spacy Installment Trouble Shooting
```
Error: Failed building wheel for spacy
Reference: https://stackoverflow.com/questions/43370851/failed-building-wheel-for-spacy
Solution: pip install --no-cache-dir spacy
```
-->



## Start Services
Start Services for the FTS system
```
Start ElasticSearch
bin/elasticsearch -d

Start reids
redis-server

Start Celery
run celery as a background job
uses screen, screen -S celery
activate python3 virtual environment, source venv/bin/activate
cd webUI
(venv)$ celery -A celery_task.tasks worker --loglevel=info
Detach from the screen,  Ctrl-a d
```

## Index Data
###Data file
Data used in the system and pretrained embedding can be downloaded from https://drive.google.com/open?id=1YzOAbUG7jFrxmDzc1Ih_QkJWSL3tjhjk and https://drive.google.com/open?id=1Gn5aklQlHlmZzRFjUv3gYfG3jkE48BP1
and put in **FTS system root folder**.



### Faceted Search
```
Faceted Search index contains 4 parts, the author index,
country index, phrase index and paper index.
Specifically country index is used in trending,
phrase index is used in phrase suggestion,
paper index is used in most of the functions.

source venv/bin/activate
(venv)$ cd webUI/src
(venv)$ python main.py
```

### SetExpan

```
source venv/bin/activate
(venv)$ python ./webUI/SetExpan/main.py
```

## Demo webUI

To start the webUI, in the **FTS system root folder**, type:

```
$ source venv/bin/activate
(venv)$ export APPLICATION_SETTINGS=config.py
(venv)$ python webUI/app.py
Use -port xxx to specify the port, by default is port 5002

To run webUI in background, with screen
screen -S webUI
$ source venv/bin/activate
(venv)$ export APPLICATION_SETTINGS=config.py
(venv)$ python webUI/app.py
Detach from the screen,  Ctrl-a d

The system is accessable on the corresponding port.

User could use bash to excute two commands at a time
(venv)$ bash webUI/start_server.sh

```
