from rest_framework import viewsets, permissions, filters
from .models import BusinessProfile, BusinessReview
from .serializers import BusinessProfileSerializer, BusinessReviewSerializer

class BusinessProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing business profiles."""
    serializer_class = BusinessProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'city', 'country']

    def get_queryset(self):
        # Allow filtering by owner
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            return BusinessProfile.objects.filter(owner_id=owner_id)
        return BusinessProfile.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class BusinessReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for business reviews, separated by module."""
    serializer_class = BusinessReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = BusinessReview.objects.all()
        
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
            
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
