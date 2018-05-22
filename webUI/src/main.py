from index_author import create_author_index
from index_author import index_author_data
from index_author import search_author_data
from index_country import create_country_index
from index_country import index_country_data
from index_country import search_country_data
from index_paper import create_inedx
from index_paper import index_data
from index_paper import search_data
from index_phrase import create_phrase_index
from index_phrase import index_phrase_data

if __name__ == '__main__':
    print('processing author index...')
    create_author_index()
    index_author_data()
    search_author_data()
    print('processing country index...')
    create_country_index()
    index_country_data()
    search_country_data()
    print('processing phrase index...')
    create_phrase_index()
    index_phrase_data()
    print('processing paper index...')
    create_inedx()
    index_data()
    search_data()
