from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleTypeViewSet, MakeViewSet, ModelViewSet,
    GearboxViewSet, BodyTypeViewSet, ColorViewSet,
    FuelTypeViewSet, SellerTypeViewSet, VehicleViewSet,
    FavoriteViewSet
)

router = DefaultRouter()
router.register(r'vehicle-types', VehicleTypeViewSet, basename='vehicletype')
router.register(r'makes', MakeViewSet, basename='make')
router.register(r'models', ModelViewSet, basename='model')
router.register(r'gearboxes', GearboxViewSet, basename='gearbox')
router.register(r'body-types', BodyTypeViewSet, basename='bodytype')
router.register(r'colors', ColorViewSet, basename='color')
router.register(r'fuel-types', FuelTypeViewSet, basename='fueltype')
router.register(r'seller-types', SellerTypeViewSet, basename='sellertype')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
