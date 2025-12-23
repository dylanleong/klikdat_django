from django.urls import path, include
from rest_framework.routers import SimpleRouter
from geo.views import GeoKlikViewSet

router = SimpleRouter()
router.register(r'geoklik', GeoKlikViewSet, basename='geoklik')

urlpatterns = [
    path('', include(router.urls)),
]
