from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from .models import ObserbatoryModel
from osiris.settings import ELASTICSEARCH_MAIN_INDEX
# Create your views here.
class ObservatoryViewSet(ElasticsearchViewSet):
    
    elastic_model = ObserbatoryModel

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._index_name = ELASTICSEARCH_MAIN_INDEX + "_observatories"

    def create(self, request, *args, **kwargs):

        client = self.get_elasticsearch_client()

        if not client.indices.exists(index=self._index_name):  
            client.indices.create(index=self._index_name)

        return super().create(request, *args, **kwargs)
    