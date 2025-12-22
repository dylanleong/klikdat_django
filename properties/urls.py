from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, SavedPropertyViewSet, PropertySavedSearchViewSet

router = DefaultRouter()
router.register(r'listings', PropertyViewSet, basename='property')
router.register(r'saved-properties', SavedPropertyViewSet, basename='saved-property')
router.register(r'saved-searches', PropertySavedSearchViewSet, basename='property-saved-search')

urlpatterns = [
    path('', include(router.urls)),
]
