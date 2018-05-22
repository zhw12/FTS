import json

papers_file = '/home/hanwen/Desktop/demo/papers-2017-02-21.json'
downsized_file = '/home/hanwen/Desktop/demo/semantic_scholar_input.txt'

f = open(papers_file)
ff = open(downsized_file, 'w')

print('Start processing...')
cnt = 0
for line in f:
    data = json.loads(line)
    year = data.get('year', 0)
    abstract = data.get('paperAbstract', '')
    venue = data.get('venue', '')
    title = data.get('title', '')
    pdfUrls = data.get('pdfUrls', '')
    s2Url = data.get('s2Url', '')
    authors = data.get('authors', '')
    if year >= 2000 and authors and title and venue and year and pdfUrls and s2Url and len(abstract) > 50:
        title = title.replace('\n', ' ').replace('\r', ' ').encode('utf-8')
        abstract = abstract.replace('\n', ' ').replace(
            '\r', ' ').encode('utf-8')
        ff.write(title + '\t' + abstract + '\n')
    if cnt % 100000 == 0:
        print('processing #%d paper'%cnt)
    cnt += 1

print('processing finished...')
