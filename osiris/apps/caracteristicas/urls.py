from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CaracteristicaViewSet


router = DefaultRouter()
router.register(r"caracteristicas", CaracteristicaViewSet, basename="caracteristicas")


urlpatterns = [
    path("", include(router.urls)),
]
