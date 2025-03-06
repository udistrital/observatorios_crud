from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, GraficoViewSet
from django.urls import path

router = DefaultRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboards')

urlpatterns = [


    path('graficos/<str:dashboard_id>/', GraficoViewSet.as_view({'get': 'list', 'post': 'create'})),

    path('graficos/<str:dashboard_id>/<str:pk>/', GraficoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

] + router.urls
