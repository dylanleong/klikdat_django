from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessProfileViewSet, BusinessReviewViewSet

router = DefaultRouter()
router.register(r'profiles', BusinessProfileViewSet, basename='business-profile')
router.register(r'reviews', BusinessReviewViewSet, basename='business-review')

urlpatterns = [
    path('', include(router.urls)),
]
