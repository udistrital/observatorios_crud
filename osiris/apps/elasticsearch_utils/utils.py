from elasticsearch import Elasticsearch
from django.conf import settings

def get_elasticsearch_client():
    return Elasticsearch(settings.ES_HOST)