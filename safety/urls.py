from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SafetyCircleViewSet

router = DefaultRouter()
router.register(r'circles', SafetyCircleViewSet, basename='safety-circle')

urlpatterns = [
    path('', include(router.urls)),
]
