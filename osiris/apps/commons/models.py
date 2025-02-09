from django.db import models
from abc import ABC, abstractmethod

class ElasticAbstracModelClass(ABC):

    @abstractmethod
    def hacer_sonido(self):
        pass
