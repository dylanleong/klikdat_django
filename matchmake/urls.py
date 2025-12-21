from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchmakeProfileViewSet, DiscoveryViewSet, SwipeViewSet, MatchViewSet

router = DefaultRouter()
router.register('profiles', MatchmakeProfileViewSet, basename='matchmake-profile')
router.register('discovery', DiscoveryViewSet, basename='matchmake-discovery')
router.register('swipes', SwipeViewSet, basename='matchmake-swipe')
router.register('matches', MatchViewSet, basename='matchmake-match')

urlpatterns = [
    path('', include(router.urls)),
]
