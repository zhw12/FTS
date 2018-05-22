input_phrase_file='../AutoPhrase/models/DBLP/AutoPhrase.txt'
output_phrase_file='linked_results.wiki.txt'
output_keywords_file='keywords.txt'

python3 wikiLinker.py $input_phrase_file $output_phrase_file
python3 generate_linked_keywords.py $output_phrase_file $output_keywords_file 