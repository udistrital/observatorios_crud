from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EstructuraViewSet


router = DefaultRouter()
router.register(r"estructuras-evidencias",EstructuraViewSet,basename="estructuras-evidencias")


urlpatterns = [
    path("", include(router.urls)),
]
