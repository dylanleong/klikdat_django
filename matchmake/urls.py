from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MatchmakeProfileViewSet, DiscoveryViewSet, SwipeViewSet, 
    MatchViewSet, MatchmakePhotoViewSet, InterestViewSet
)

router = DefaultRouter()
router.register('profiles', MatchmakeProfileViewSet, basename='matchmake-profile')
router.register('discovery', DiscoveryViewSet, basename='matchmake-discovery')
router.register('swipes', SwipeViewSet, basename='matchmake-swipe')
router.register('matches', MatchViewSet, basename='matchmake-match')
router.register('photos', MatchmakePhotoViewSet, basename='matchmake-photo')
router.register('interests', InterestViewSet, basename='matchmake-interest')

urlpatterns = [
    path('', include(router.urls)),
]
