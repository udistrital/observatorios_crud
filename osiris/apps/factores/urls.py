from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FactorViewSet


router = DefaultRouter()
router.register(r"factores", FactorViewSet, basename="Factor")


urlpatterns = [
    path("", include(router.urls)),
]
