from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ObservatoryViewSet

router = DefaultRouter()
router.register(r'observatories', ObservatoryViewSet, basename='Observatory')

urlpatterns = [
] + router.urls