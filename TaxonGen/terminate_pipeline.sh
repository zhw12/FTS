#!/usr/bin/env bash
killChildProcess(){
    ps --ppid $1 | awk '{if($1~/[0-9]+/) print $1}'| xargs kill -9
#    ps --ppid $1
    echo '----'
    kill -9 $1
}

for var in "local-embedding" "auto_phrase.sh" "phrasal_segmentation.sh" "run.sh" "taxongen_pipeline.py" "wikiLinker.py"
do
#   | xargs kill -9
    for pid in `ps -ef | grep $var  | awk '{print $2}'`
    do
        killChildProcess $pid
    done
done