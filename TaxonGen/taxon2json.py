'''
    from taxonomy_ids.txt to json
'''
import json
import os
import re
import argparse
import base64
import sys
'''
    Example Line:
    */large_scale_distributed_systems	large_scale_distributed_systems,software_engineering,agile_development,software_development,software_process_improvement,software_process,agile_methods,requirements_engineering,web_services,software_reuse
'''

# runned in tasks.py --> taxongen_piepline.py --> taxon2json
# taxon2json path is in its own directory
root_dir = os.path.abspath('..')
sys.path.append('{}/webUI/'.format(root_dir))
from utils.utils import is_single_query, encode_filename, decode_filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    query = args.query.replace(' ', '_')
    input_file_path = root_dir + '/' + 'local-embedding/data/%s/taxonomies/l3-no-local-emb.txt'%query
    output_file_path = root_dir + '/' + 'data/generated_taxonomy/tree_%s.json'%query
    links = []
    nodes = dict()
    id2path = {}
    cnt = 1

    raw_query, _ = decode_filename(query)

    root_name = raw_query

    # root_name = query.replace('_', ' ')
    nodes[root_name] = {

        'path': root_name,
        'name': root_name,
        'keywords': []
    }

    with open(input_file_path) as f:
        for line in f:
            meta = re.split(pattern='\t', string=line)
            # taxonID = meta[0]
            path_raw = meta[0][2:]
            path = path_raw.rsplit('/', 1)

            if not path:
                continue
            id2path[cnt] = path_raw
            # level = taxonID[0]
            nodes[path_raw] = {
                # 'taxonID': taxonID,
                # 'level': level,
                'path': meta[0][2:],
                'keywords': [key.replace('_', ' ') for key in meta[1].strip().split(',')],
                'name': path[-1].replace('_', ' ')
            }
            if len(path) >= 2:
                links.append((path[0], path_raw))
            elif len(path) == 1:
                links.append((root_name, path_raw))
            cnt += 1

    deduplicate_links = []
    for link in links:
        if link[0] == link[1]:
            continue
        if link not in deduplicate_links:
            deduplicate_links.append(link)
    links = deduplicate_links


    def get_nodes(node):
        # d = {}
        # d['name'] = node
        d = nodes[node].copy()
        children = get_children(node)
        if children:
            d['children'] = [get_nodes(child) for child in children]
        else:
            children_data = []
            for c in d['keywords']:
                children_data.append({'name':c, 'children':[], 'path': d['path'] + '/' + c.replace(' ', '_'), 'keywords':[c]})
            d['children'] = children_data
        return d


    def get_children(node):
        return [x[1] for x in links if x[0] == node]

    tree = get_nodes(root_name)
    # print(json.dumps(tree, indent=4))

    with open(output_file_path, 'w') as fout:
        json.dump(tree, fout)
    print('finish transforming taxonomy file to json...')


# cp data/quantum_tree.json webUI/static/tree_quantum_learning.json
# cp data/quantum_id2path.json webUI/static/
