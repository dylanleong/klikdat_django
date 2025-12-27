from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, VerificationViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'verification', VerificationViewSet, basename='verification')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
