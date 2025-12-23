from rest_framework import serializers
from .models import Property, PropertyImage, SavedProperty, PropertySavedSearch
from business.serializers import BusinessProfileSerializer
from django.contrib.auth.models import User

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_primary', 'created_at']

class PropertySerializer(serializers.ModelSerializer):
    business_details = BusinessProfileSerializer(source='business', read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    agent_name = serializers.CharField(source='agent.username', read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Property
        fields = [
            'id', 'business', 'business_details', 'agent', 'agent_name',
            'title', 'description', 'listing_type', 'property_type', 'category',
            'price', 'currency', 'price_qualifier',
            'bedrooms', 'bathrooms', 'area_sqft',
            'location', 'latitude', 'longitude', 'features', 'status',
            'images', 'uploaded_images', 'floor_plan', 'created_at', 'updated_at'
        ]
        read_only_fields = ['business', 'agent', 'created_at', 'updated_at']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        property_instance = super().create(validated_data)
        
        for index, image in enumerate(uploaded_images):
            PropertyImage.objects.create(
                property=property_instance, 
                image=image, 
                is_primary=(index == 0)
            )
        return property_instance

class SavedPropertySerializer(serializers.ModelSerializer):
    property_details = PropertySerializer(source='property', read_only=True)

    class Meta:
        model = SavedProperty
        fields = ['id', 'property', 'property_details', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PropertySavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySavedSearch
        fields = ['id', 'name', 'query_params', 'notifications_enabled', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
