from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import (
    VehicleType, Make, Model,
    SellerType, Vehicle, VehicleImage, Favorite, VehicleProfile
)
from .models_attributes import VehicleAttribute
from .serializers import (
    VehicleTypeSerializer, MakeSerializer, ModelSerializer,
    SellerTypeSerializer, VehicleSerializer,
    VehicleImageSerializer, FavoriteSerializer, VehicleAttributeSerializer,
    VehicleProfileSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class VehicleTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle types (Car, Motorcycle, Van, Truck)"""
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MakeViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle manufacturers"""
    queryset = Make.objects.all()
    serializer_class = MakeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Allow filtering by vehicle_type
        vehicle_type_id = self.request.query_params.get('vehicle_type', None)
        if vehicle_type_id is not None:
            queryset = queryset.filter(vehicle_types=vehicle_type_id)
        return queryset


class ModelViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle models"""
    queryset = Model.objects.select_related('make').all()
    serializer_class = ModelSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Allow filtering by make
        make_id = self.request.query_params.get('make', None)
        if make_id is not None:
            queryset = queryset.filter(make_id=make_id)
            
        # Allow filtering by vehicle_type
        vehicle_type_id = self.request.query_params.get('vehicle_type', None)
        if vehicle_type_id is not None:
            queryset = queryset.filter(vehicle_type_id=vehicle_type_id)
            
        return queryset
        return queryset



class SellerTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for seller types"""
    queryset = SellerType.objects.all()
    serializer_class = SellerTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class VehicleProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user vehicle profiles"""
    serializer_class = VehicleProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # User can only see their own profile
        return VehicleProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VehicleAttributeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving dynamic vehicle attributes.
    Filterable by vehicle_type (ID).
    Example: /api/attributes/?vehicle_type=1
    """
    queryset = VehicleAttribute.objects.prefetch_related('options').all()
    serializer_class = VehicleAttributeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        vehicle_type_id = self.request.query_params.get('vehicle_type', None)
        if vehicle_type_id:
            queryset = queryset.filter(vehicle_types__id=vehicle_type_id)
        return queryset


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle listings"""
    queryset = Vehicle.objects.select_related(
        'owner', 'vehicle_type', 'make', 'model', 'seller_type'
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

        # Dynamic Attribute Filtering
        # Iterate over all registered attributes and check if they are in query params
        # This assumes attributes are relatively stable. For high performace, cache definitions.
        # Note: This allows filtering by ANY attribute defined in the system.
        
        # We need to filter for specifications__{slug} = value
        # But we only want to do this for valid attributes to avoid conflict with other params
        # A simple approach is to iterate request.query_params
        
        reserved_params = {
            'page', 'limit', 'ordering', 'search', 
            'owner', 'vehicle_type', 'make', 
            'min_price', 'max_price', 
            'min_year', 'max_year', 
            'min_mileage', 'max_mileage',
            'location'
        }
        
        for key, value in self.request.query_params.items():
            if key not in reserved_params and value:
                # Assume it's a dynamic attribute (or ignore if not found? existing behavior was safe)
                # To be safe, we could check if VehicleAttribute exists with this slug,
                # but that adds a DB query per request.
                # Let's try to filter on specifications directly.
                # Django JSONField filtering: specifications__color="red"
                kwargs = {f"specifications__{key}": value}
                try:
                    queryset = queryset.filter(**kwargs)
                except Exception:
                    # Ignore invalid filters that might crash JSON lookup (unlikely with this syntax)
                    pass
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        # Calculate Facets
        # We calculate facets on the *filtered* queryset (to show available options within current filter)
        # OR on the *unfiltered* (or partially filtered) queryset depending on UX requirements.
        # usually "faceted search" means showing counts for specific filters based on current constraints.
        
        # However, to prevent "narrowing to zero" where you can't unselect or select siblings,
        # typically you want counts for a dimension *excluding* the filter on that dimension.
        # But for simplicity in this MVP, we will calculate counts on the currently filtered queryset
        # which effectively shows "what's left". 
        
        # NOTE: If the user filters by Make=Toyota, the Make facet will only show Toyota (count=N).
        # This is expected behavior for a simple "Drill down". 
        # For "Multi-select" usually you want counts over the whole set.
        # Let's stick to the filtered set for now as it's efficient and standard for basic drill-down.
        
        from django.db.models import Count
        
        facets = {}
        
        # 1. Standard Fields
        # Make
        facets['makes'] = queryset.values('make__id', 'make__make').annotate(count=Count('id')).order_by('-count')
        # Models
        facets['models'] = queryset.values('model__id', 'model__model').annotate(count=Count('id')).order_by('-count')
        # Vehicle Type
        facets['vehicle_types'] = queryset.values('vehicle_type__id', 'vehicle_type__vehicle_type').annotate(count=Count('id')).order_by('-count')
        # Seller Type
        facets['seller_types'] = queryset.values('seller_type__id', 'seller_type__seller_type').annotate(count=Count('id')).order_by('-count')
        # Year
        facets['years'] = queryset.values('year').annotate(count=Count('id')).order_by('-year')
        
        # 2. Dynamic Attributes (from specifications)
        # We need to filter which attributes to facet on. 
        # Ideally, only facet on attributes relevant to the current vehicle_type (if selected) or top-level ones.
        # For now, let's grab all defined VehicleAttributes and try to aggregate.
        # Warning: iterating all definitions might be slow if there are hundreds.
        
        attributes = VehicleAttribute.objects.all()
        # If vehicle_type is filtered, we could restrict attributes to just those 
        # (but cross-type search might be interesting).
        
        dynamic_facets = {}
        for attr in attributes:
            # We aggregate on specifications__{slug}
            # Note: values() on JSON field path works in Postgres and recent SQLite
            key = f"specifications__{attr.slug}"
            
            # We only want values that are not null/None. 
            # Note: We can't easily filter out "null" keys in JSON unless we do strict filtering.
            # But the annotate should handle grouping by unique values found.
            
            try:
                counts = queryset.values(key).annotate(count=Count('id')).order_by('-count')
                
                # Transform to cleaner format: [{"value": "Red", "count": 5}, ...]
                facet_values = []
                for item in counts:
                    val = item.get(key)
                    if val is not None:
                        facet_values.append({'value': val, 'count': item['count']})
                
                if facet_values:
                    dynamic_facets[attr.slug] = facet_values
            except Exception:
                # Fallback if DB doesn't support this specific JSON Op or empty result issues
                pass
                
        facets['specifications'] = dynamic_facets
        
        # Inject validation into response
        # Check if response.data is a dict (Pagination) or list (No Pagination)
        if isinstance(response.data, dict):
             response.data['facets'] = facets
        else:
             # Wrap list in object
             response.data = {
                 'results': response.data,
                 'facets': facets
             }

        return response
    
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
