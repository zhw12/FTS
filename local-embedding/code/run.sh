#!/bin/bash
## Name of the input corpus
# corpusName=quantum_sensing
corpusName=${corpusName:- test}
## Name of the taxonomy
taxonName=l3-no-local-emb
## If need preprocessing from raw input, set it to be 1, otherwise, set 0
FIRST_RUN=${FIRST_RUN:- 1}

if [ $FIRST_RUN -eq 1 ]; then
	echo 'Start data preprocessing'
	## compile word2vec for embedding learning
	gcc word2vec.c -o word2veec -lm -pthread -O2 -Wall -funroll-loops -Wno-unused-result

	## create initial folder if not exist
	if [ ! -d ../data/$corpusName/init ]; then
		mkdir ../data/$corpusName/init
	fi

	echo 'Start cluster-preprocess.py'
	time python cluster-preprocess.py $corpusName

	echo 'Start preprocess.py'
	time python preprocess.py $corpusName

	cp ../data/$corpusName/input/embeddings.txt ../data/$corpusName/init/embeddings.txt
	cp ../data/$corpusName/input/keywords.txt ../data/$corpusName/init/seed_keywords.txt
fi

## create root folder for taxonomy
if [ ! -d ../data/$corpusName/$taxonName ]; then
	mkdir ../data/$corpusName/$taxonName
fi

root_dir=`python -c "import os; print os.path.abspath('../..')"`
echo 'Start TaxonGen'
#python2 main.py
../../venv_py2/bin/python main.py --data_dir "${root_dir}/local-embedding/data/${corpusName}/"

echo 'Generate compressed taxonomy'
if [ ! -d ../data/$corpusName/taxonomies ]; then
	mkdir ../data/$corpusName/taxonomies
fi
# python2 compress.py -root ../data/$corpusName/$taxonName -output ../data/$corpusName/taxonomies/$taxonName.txt
../../venv_py2/bin/python compress.py -root ../data/$corpusName/$taxonName -output ../data/$corpusName/taxonomies/$taxonName.txt -corpus ../data/$corpusName/input/papers.txt

#export corpusName=deep_learning
#export taxonName=l3-no-local-emb
#python2 compress.py -root ../data/$corpusName/$taxonName -output ../data/$corpusName/taxonomies/$taxonName.txt -corpus ../data/$corpusName/input/papers.txt
