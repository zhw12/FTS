query=$1
root_dir=${root_dir:- "/home/hanwen/disk/demov3"}
rm ${root_dir}/TaxonGen/taxongen_task_list.txt
rm ${root_dir}/TaxonGen/taxongen_pipeline.log
rm ${root_dir}/data/generated_taxonomy/tree_${query}.json $query
rm -r ${root_dir}/local-embedding/data/${query}