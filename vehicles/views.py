from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import (
    VehicleType, Make, Model, Gearbox, BodyType,
    Color, FuelType, SellerType, Vehicle, VehicleImage, Favorite
)
from .serializers import (
    VehicleTypeSerializer, MakeSerializer, ModelSerializer,
    GearboxSerializer, BodyTypeSerializer, ColorSerializer,
    FuelTypeSerializer, SellerTypeSerializer, VehicleSerializer,
    VehicleImageSerializer, FavoriteSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class VehicleTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle types (Car, Motorcycle, Van, Truck)"""
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MakeViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle manufacturers"""
    queryset = Make.objects.all()
    serializer_class = MakeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ModelViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle models"""
    queryset = Model.objects.select_related('make').all()
    serializer_class = ModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Allow filtering by make
        make_id = self.request.query_params.get('make', None)
        if make_id is not None:
            queryset = queryset.filter(make_id=make_id)
        return queryset


class GearboxViewSet(viewsets.ModelViewSet):
    """ViewSet for gearbox types"""
    queryset = Gearbox.objects.all()
    serializer_class = GearboxSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BodyTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for body types"""
    queryset = BodyType.objects.all()
    serializer_class = BodyTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ColorViewSet(viewsets.ModelViewSet):
    """ViewSet for colors"""
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class FuelTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for fuel types"""
    queryset = FuelType.objects.all()
    serializer_class = FuelTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SellerTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for seller types"""
    queryset = SellerType.objects.all()
    serializer_class = SellerTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle listings"""
    queryset = Vehicle.objects.select_related(
        'owner', 'vehicle_type', 'make', 'model', 'gearbox',
        'body_type', 'color', 'fuel_type', 'seller_type'
    ).prefetch_related('images').all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['make__name', 'model__name', 'location', 'year']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by owner if requested
        owner_id = self.request.query_params.get('owner', None)
        if owner_id is not None:
            queryset = queryset.filter(owner_id=owner_id)
        
        # Filter by vehicle type
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type is not None:
            queryset = queryset.filter(vehicle_type_id=vehicle_type)
        
        # Filter by make
        make = self.request.query_params.get('make', None)
        if make is not None:
            queryset = queryset.filter(make_id=make)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by year range
        min_year = self.request.query_params.get('min_year', None)
        max_year = self.request.query_params.get('max_year', None)
        if min_year is not None:
            queryset = queryset.filter(year__gte=min_year)
        if max_year is not None:
            queryset = queryset.filter(year__lte=max_year)
            
        # Filter by mileage range
        min_mileage = self.request.query_params.get('min_mileage', None)
        max_mileage = self.request.query_params.get('max_mileage', None)
        if min_mileage is not None:
            queryset = queryset.filter(mileage__gte=min_mileage)
        if max_mileage is not None:
            queryset = queryset.filter(mileage__lte=max_mileage)
            
        # Filter by location (partial match)
        location = self.request.query_params.get('location', None)
        if location is not None:
            queryset = queryset.filter(location__icontains=location)
        
        return queryset
    
    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)
    
    def perform_update(self, serializer):
        # Only allow owners to update their own vehicles
        if serializer.instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own vehicles.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only allow owners to delete their own vehicles
        if instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own vehicles.")
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_image(self, request, pk=None):
        """Upload an image for a vehicle"""
        vehicle = self.get_object()
        
        # Check ownership
        if vehicle.owner != request.user:
            return Response(
                {"detail": "You can only upload images for your own vehicles."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = VehicleImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Toggle favorite status for a vehicle"""
        vehicle = self.get_object()
        user = request.user
        
        favorite, created = Favorite.objects.get_or_create(user=user, vehicle=vehicle)
        
        if not created:
            # If already favorited, remove it
            favorite.delete()
            return Response({"status": "removed from favorites"}, status=status.HTTP_200_OK)
            
        return Response({"status": "added to favorites"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def contact(self, request, pk=None):
        """Initiate contact with the seller"""
        vehicle = self.get_object()
        buyer = request.user
        seller = vehicle.owner
        
        if buyer == seller:
            return Response(
                {"detail": "You cannot contact yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # This assumes the chat app has a Room model and create_room logic
        # We'll import it dynamically to avoid circular imports if possible
        # or just use the models directly if we know the structure
        try:
            from chat.models import Room, Message
            
            # Check if room exists between these users
            # This is a simplified check - a real implementation might be more complex
            # depending on how rooms are structured (e.g. many-to-many users)
            
            # For now, let's assume we create a new room or get existing
            # We'll need to adapt this based on the actual chat app implementation
            # Let's try to find a room with both users
            
            room = Room.objects.filter(participants=buyer).filter(participants=seller).first()
            
            if not room:
                room = Room.objects.create()
                room.participants.add(buyer, seller)
                
                # Send initial message
                initial_text = f"Hi, I'm interested in your {vehicle.year} {vehicle.make.make} {vehicle.model.model} listed for ${vehicle.price}."
                Message.objects.create(room=room, sender=buyer, content=initial_text)
                
            return Response({"room_id": room.id}, status=status.HTTP_200_OK)
            
        except ImportError:
            return Response(
                {"detail": "Chat module not available."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user's favorite vehicles"""
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related(
            'vehicle', 'vehicle__make', 'vehicle__model'
        )
