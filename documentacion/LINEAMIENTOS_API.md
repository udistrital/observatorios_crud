Lineamientos para una API en Django

1. ¿Qué es una App en Django?

Una app en Django es un módulo independiente que encapsula una funcionalidad específica dentro de un proyecto. Puede ser reutilizada en diferentes proyectos y comunicarse con otras apps dentro del mismo proyecto.

Para crear una nueva app en Django, se usa el siguiente comando:

python manage.py startapp nombre_de_la_app

2. Organización de las Apps

Se recomienda organizar las apps dentro de una carpeta llamada apps para mantener una estructura ordenada y modular. Ejemplo de jerarquía de directorios:

mi_proyecto/
│── manage.py
│── mi_proyecto/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
└── apps/
    ├── app1/
    │   ├── migrations/
    │   ├── models.py
    │   ├── views.py
    │   ├── serializers.py
    │   ├── urls.py
    │   ├── tests.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── permissions.py
    │   ├── filters.py
    │   ├── signals.py
    │   ├── __init__.py
    │
    ├── app2/
    │   ├── ...

Para que Django reconozca las apps dentro de la carpeta apps, es necesario agregarlas en INSTALLED_APPS dentro del archivo settings.py:

INSTALLED_APPS = [
    'apps.app1',
    'apps.app2',
    # Otras apps...
]

3. Explicación de los Archivos en una App

Cada app en Django contiene varios archivos clave:

models.py

Define los modelos de base de datos de la app usando Django ORM.

Ejemplo:

from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)

views.py

Contiene las vistas de la API. En el caso de Django REST Framework (DRF), suele usar ViewSets.

Ejemplo:

from rest_framework.viewsets import ModelViewSet
from .models import Producto
from .serializers import ProductoSerializer

class ProductoViewSet(ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

serializers.py

Define los serializadores para convertir modelos en JSON y viceversa.

Ejemplo:

from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

urls.py

Define las rutas de la API para la app.

Ejemplo:

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

admin.py

Registra modelos para que sean administrados desde el panel de administración de Django.

Ejemplo:

from django.contrib import admin
from .models import Producto

admin.site.register(Producto)

apps.py

Configuración de la app.

Ejemplo:

from django.apps import AppConfig

class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.app1'

migrations/

Contiene archivos generados por Django para gestionar cambios en la base de datos.

Ejemplo:

python manage.py makemigrations
python manage.py migrate

tests.py

Contiene pruebas unitarias para verificar el funcionamiento de la app.

Ejemplo:

from django.test import TestCase

class ProductoTestCase(TestCase):
    def test_creacion_producto(self):
        self.assertEqual(1, 1)  # Prueba simple

permissions.py (Opcional)

Define permisos personalizados para la API.

Ejemplo:

from rest_framework.permissions import BasePermission

class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff

filters.py (Opcional)

Define filtros para la API.

Ejemplo:

from django_filters import rest_framework as filters
from .models import Producto

class ProductoFilter(filters.FilterSet):
    class Meta:
        model = Producto
        fields = ['nombre', 'precio']

signals.py (Opcional)

Define señales para ejecutar acciones cuando ocurren ciertos eventos en la base de datos.

Ejemplo:

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producto

@receiver(post_save, sender=Producto)
def producto_guardado(sender, instance, created, **kwargs):
    print(f'Producto {instance.nombre} guardado.')

Conclusión

Siguiendo esta estructura y buenas prácticas, se puede desarrollar una API bien organizada y escalable en Django.