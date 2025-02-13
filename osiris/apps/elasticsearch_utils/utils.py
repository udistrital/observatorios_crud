from elasticsearch import Elasticsearch
from django.conf import settings

def get_elasticsearch_client():
    return Elasticsearch([{
        'host': settings.ELASTICSEARCH_HOST,
        'port': settings.ELASTICSEARCH_PORT,
    }])