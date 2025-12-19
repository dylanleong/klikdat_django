from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleTypeViewSet, MakeViewSet, ModelViewSet,
    SellerTypeViewSet, VehicleViewSet,
    VehicleAttributeViewSet, 
    SellerProfileViewSet, BuyerProfileViewSet,
    SavedSearchViewSet, SellerReviewViewSet,
    SavedVehicleViewSet
)

router = DefaultRouter()
router.register(r'vehicle-types', VehicleTypeViewSet, basename='vehicletype')
router.register(r'makes', MakeViewSet, basename='make')
router.register(r'models', ModelViewSet, basename='model')
router.register(r'seller-types', SellerTypeViewSet, basename='sellertype')
router.register(r'saved-vehicles', SavedVehicleViewSet, basename='savedvehicle')
router.register(r'attributes', VehicleAttributeViewSet, basename='attribute')
router.register(r'seller-profiles', SellerProfileViewSet, basename='sellerprofile')
router.register(r'buyer-profiles', BuyerProfileViewSet, basename='buyerprofile')
router.register(r'saved-searches', SavedSearchViewSet, basename='savedsearch')
router.register(r'seller-reviews', SellerReviewViewSet, basename='sellerreview')
router.register(r'', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
