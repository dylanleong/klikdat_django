from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleTypeViewSet, MakeViewSet, ModelViewSet,
    SellerTypeViewSet, VehicleViewSet,
    FavoriteViewSet, VehicleAttributeViewSet, VehicleProfileViewSet
)

router = DefaultRouter()
router.register(r'vehicle-types', VehicleTypeViewSet, basename='vehicletype')
router.register(r'makes', MakeViewSet, basename='make')
router.register(r'models', ModelViewSet, basename='model')
router.register(r'seller-types', SellerTypeViewSet, basename='sellertype')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'attributes', VehicleAttributeViewSet, basename='attribute')
router.register(r'vehicle-profiles', VehicleProfileViewSet, basename='vehicleprofile')
router.register(r'', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
