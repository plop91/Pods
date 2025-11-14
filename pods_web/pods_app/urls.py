"""URL configuration for Pods app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for the API endpoints
router = DefaultRouter()
router.register(r'api/pods', views.PodViewSet, basename='pod')
router.register(r'api/relationships', views.RelationshipViewSet, basename='relationship')

urlpatterns = [
    path('', views.index, name='index'),
    path('', include(router.urls)),
]
