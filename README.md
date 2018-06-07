# FTS-Demo
The Demo System for Faceted Taxonomy and Search

Online demo: <http://dhcp-54-50.cs.ucsb.edu:5002/>

## Getting Started
This is an instruction for offline deployment of the 
FTS (Faceted Taxonomy and Search) Demo System. 
The instruction uses Linux as an example.

### Requirements
Main requirements:
- python3
- python2
- elasticsearch
- redis
- celery
- gensim
- spacy


Other python requirements:
- python3: webUI/requirements.txt
- python2: webUI/requirements_python2.txt

### Installation
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
```


#### Python requirements
```
In root folder, Create the virtual environments venv, venv_py2,
()

virtualenv --python=/usr/bin/python2 venv_py2
virtualenv --python=/usr/bin/python3 venv
 
Install requirements for python3:
source venv/bin/activate
(venv)$ pip install -r webUI/requirements.txt
 
Install requirements for python2:
source venv_py2/bin/activate
(venv_py2)$ pip install -r webUI/requirements_python2.txt
```

#### Spacy
Use spacy to de text processing
```
Install spacy in python3
Enter python3 virtual environment, source venv/bin/activate
(venv)$ pip install spacy
Download spacy model file
(venv)$ python -m spacy download en
```

## Start Services
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
Data file: download embedding and data folder from ftp server:
<ftp://dhcp-54-50.cs.ucsb.edu:5003>

put them in the **demo root folder**
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

To start the webUI, in the **demo root folder**, type:

```
$ source venv/bin/activate
(venv)$ python webUI/app.py
Use -port xxx to specify the port, by default is port 5002
 
To run webUI in background, with screen
screen -S webUI
$ source venv/bin/activate
(venv)$ python webUI/app.py
Detach from the screen,  Ctrl-a d
 
The demo is accessable on the corresponding port.
```
