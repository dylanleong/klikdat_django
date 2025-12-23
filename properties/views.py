from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from .models import Property, SavedProperty, PropertySavedSearch, PropertyImage
from .serializers import (
    PropertySerializer, SavedPropertySerializer, PropertySavedSearchSerializer,
    PropertyImageSerializer
)
from business.models import BusinessProfile

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all().order_by('-created_at')
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'location', 'features']

    def perform_create(self, serializer):
        # Automatically link to Agent's Business
        business = BusinessProfile.objects.filter(owner=self.request.user).first()
        if not business:
            raise serializers.ValidationError("You must have a Business Profile to list properties.")
        
        serializer.save(agent=self.request.user, business=business)

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Public filtering
        listing_type = self.request.query_params.get('listing_type')
        if listing_type:
            queryset = queryset.filter(listing_type=listing_type)
            
        property_type = self.request.query_params.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
            
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_listings(self, request):
        """List properties created by the logged-in agent"""
        queryset = self.get_queryset().filter(agent=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def broadcast(self, request, pk=None):
        """
        Notify users who:
        1. Have saved this property.
        2. Have a saved search that matches this property (simplified check).
        """
        property_instance = self.get_object()
        
        # Only owner can broadcast
        if property_instance.agent != request.user:
             return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        message_body = request.data.get('message', f"Update on {property_instance.title}")
        
        # 1. Users who saved this property
        saved_users = [sp.user for sp in property_instance.saved_by.all()]
        
        # 2. Users with matching saved searches (Simplified: Just checking keywords/type)
        # In a real app, we would run the search query against this property
        # For prototype, we'll just check if their saved search queries match property features crudely
        potential_searches = PropertySavedSearch.objects.filter(
            notifications_enabled=True
        ).exclude(user__in=saved_users) # Don't double notify
        
        matched_search_users = []
        for search in potential_searches:
            # Very basic check: if property Listing Type matches search
            params = search.query_params
            if isinstance(params, str):
                import json
                try:
                    params = json.loads(params)
                except:
                    continue

            if params.get('listing_type') == property_instance.listing_type:
                 matched_search_users.append(search.user)

        target_users = set(saved_users + matched_search_users)
        
        # Send Notifications (Email Simulation)
        email_count = 0
        for user in target_users:
            if user.email:
                send_mail(
                    subject=f"Update: {property_instance.title}",
                    message=f"Hi {user.username},\n\nAgent Update: {message_body}\n\nView Property: /properties/{property_instance.id}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True
                )
                email_count += 1
        
        return Response({
            'status': 'Broadcast sent', 
            'recipients': len(target_users),
            'emails_sent': email_count
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_image(self, request, pk=None):
        """Upload an image for a property"""
        property_instance = self.get_object()
        
        # Check ownership
        if property_instance.agent != request.user:
            return Response(
                {"detail": "You can only upload images for your own properties."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = PropertyImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(property=property_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_floor_plan(self, request, pk=None):
        """Upload a floor plan for a property"""
        property_instance = self.get_object()
        
        # Check ownership
        if property_instance.agent != request.user:
            return Response(
                {"detail": "You can only upload floor plans for your own properties."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        floor_plan = request.FILES.get('floor_plan')
        if floor_plan:
            property_instance.floor_plan = floor_plan
            property_instance.save()
            serializer = self.get_serializer(property_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "No floor plan file provided"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def delete_image(self, request, pk=None):
        """Delete an image for a property"""
        property_instance = self.get_object()
        
        # Check ownership
        if property_instance.agent != request.user:
            return Response(
                {"detail": "You can only delete images for your own properties."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        image_id = request.query_params.get('image_id')
        if not image_id:
            return Response({"error": "image_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            image = PropertyImage.objects.get(id=image_id, property=property_instance)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PropertyImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)


class SavedPropertyViewSet(viewsets.ModelViewSet):
    serializer_class = SavedPropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedProperty.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check uniqueness handled by unique_together in Model + Serializer validation
        serializer.save(user=self.request.user)


class PropertySavedSearchViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PropertySavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
