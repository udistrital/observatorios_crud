from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AspectoViewSet


router = DefaultRouter()
router.register(r"aspectos", AspectoViewSet, basename="aspectos")


urlpatterns = [
    path("", include(router.urls)),
]
