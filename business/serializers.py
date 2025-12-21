from rest_framework import serializers
from .models import BusinessProfile, BusinessReview
from django.db.models import Avg

class BusinessProfileSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    rating = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'owner', 'owner_username', 'name', 'is_private',
            'logo', 'website', 'about_us', 'contact_number', 'phone_number',
            'address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country',
            'opening_hours', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'is_private', 'created_at', 'updated_at']

    def get_rating(self, obj):
        # Default global rating across all modules
        average = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return average if average is not None else 0

class BusinessReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)
    
    class Meta:
        model = BusinessReview
        fields = [
            'id', 'business', 'reviewer', 'reviewer_username', 
            'module', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['reviewer', 'created_at']
