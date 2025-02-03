from django.db import models
from apps.elasticsearch_utils.models import ElasticField
from apps.elasticsearch_utils.models import AuditModel
# Create your models here.





class ObserbatoryModel(AuditModel):
    name =  ElasticField(str)

    

    
