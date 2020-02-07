import os
from elasticsearch import Elasticsearch

import scraper

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))

INDEX = 'documentation'

print('Establishing a connection to ES - host: {} and port: {}'.format(ES_HOST, ES_PORT))
ES = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT}])


def insert_doc(doc):
    res = ES.index(index='documentation', body=doc)
    print('Inserted doc res=' + str(res))


def create():
    print('Creating index: {}'.format(INDEX))

    res = ES.indices.create(index=INDEX, body={
        "mappings": {
            "properties": {
                "facet_name": {
                    "type": "keyword"
                },
                "facet_group": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h1": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h2": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h3": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h4": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h5": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "h6": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "content": {
                    "type": "text",
                    "analyzer": "english",
                    "fielddata": True
                },
                "rendered_content": {
                    "type": "text",
                    "analyzer": "english",
                },
                "link": {
                    "type": "text",
                },
                "base_link": {
                    "type": "text",
                },
                "type": {
                    "type": "keyword"
                },
            }
        }
    })

    print('Created index res=' + str(res))


def delete():
    print('Deleting index: {}'.format(INDEX))
    res = ES.indices.delete(index=INDEX, ignore=[400, 404])
    print('Deleted index res=' + str(res))


def search(query, facets):
    should_terms = [{"term": {"facet_name": f}} for f in facets]
    min_should_match = 0 if not should_terms else 1

    return ES.search(index=INDEX, body={
        'query': {
            'bool': {
                'must': {
                    'multi_match': {
                        'query': query,
                        'fields': [
                            "title^2",
                            "h1^1.5",
                            "h2^1.2",
                            "h3^1.2",
                            "h4^1",
                            "h5^1",
                            "h6^1",
                            "content^1",
                        ],
                        'fuzziness': "AUTO",
                        'prefix_length': 2,
                    }
                },
                'should': should_terms,
                'minimum_should_match': min_should_match,
            }
        },
        'highlight': {
            'pre_tags': ["<em>"],
            'post_tags': ["</em>"],
            'fields': {
                'title': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'content': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h1': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h2': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h3': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h4': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h5': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                },
                'h6': {
                    'fragment_size': 0,
                    'number_of_fragments': 0,
                }
            }
        },
        'size': 300
    })


def get_facets():
    return scraper.FACET_GROUPS
