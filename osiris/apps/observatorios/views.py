from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from .models import ObservatorioModelo
from osiris.settings import ELASTICSEARCH_MAIN_INDEX
# Create your views here.
class ObservatorioViewSet(ElasticsearchViewSet):
    
    elastic_model = ObservatorioModelo

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = ELASTICSEARCH_MAIN_INDEX + "_observatorios"


    def obtener_busqueda(self):
        return {
            "query" : {
                "term": {
                    "activo": True
                } }
        }

    def create(self, request, *args, **kwargs):

        client = self.get_elasticsearch_client()

        if not client.indices.exists(index=self._nombre_indice):  
            client.indices.create(index=self._nombre_indice)

        return super().create(request, *args, **kwargs)
    