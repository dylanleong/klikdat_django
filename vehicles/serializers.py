from rest_framework import serializers
from .models import (
    VehicleType, Make, Model,
    SellerType, Vehicle, VehicleImage, SavedVehicle,
    SellerProfile, BuyerProfile, SavedSearch
)
from .models_attributes import VehicleAttribute, VehicleAttributeOption


class VehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImage
        fields = ['id', 'image', 'is_primary', 'created_at']





class VehicleAttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleAttributeOption
        fields = ['id', 'label', 'value']


class VehicleAttributeSerializer(serializers.ModelSerializer):
    options = VehicleAttributeOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = VehicleAttribute
        fields = ['id', 'name', 'slug', 'attribute_type', 'is_required', 'options']


class VehicleTypeSerializer(serializers.ModelSerializer):
    attributes = VehicleAttributeSerializer(many=True, read_only=True)
    
    class Meta:
        model = VehicleType
        fields = ['id', 'vehicle_type', 'schema', 'attributes']


class MakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Make
        fields = ['id', 'make', 'vehicle_types']


class ModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.make', read_only=True)
    
    class Meta:
        model = Model
        fields = ['id', 'model', 'make', 'make_name', 'vehicle_type']


class SellerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerType
        fields = ['id', 'seller_type']


class VehicleSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    vehicle_type_name = serializers.CharField(source='vehicle_type.vehicle_type', read_only=True)
    make_name = serializers.CharField(source='make.make', read_only=True)
    model_name = serializers.CharField(source='model.model', read_only=True)
    seller_type_name = serializers.CharField(source='seller_type.seller_type', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    images = VehicleImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'owner_username',
            'business', 'business_name',
            'title', 'description',
            'vehicle_type', 'vehicle_type_name',
            'make', 'make_name',
            'model', 'model_name',
            'seller_type', 'seller_type_name',
            'price', 'year', 'mileage', 'location',
            'video_url', 'is_hidden',
            'num_doors', 'num_seats',
            'battery_range', 'charging_time',
            'engine_size', 'engine_power', 'acceleration', 'fuel_consumption',
            'tax_per_year', 'boot_space',
            'specifications',
            'created_at', 'updated_at',
            'images', 'is_favorited'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'seller_type']


    def validate(self, data):
        """
        Validate dynamic specifications against required vehicle attributes.
        """
        vehicle_type = data.get('vehicle_type')
        specifications = data.get('specifications', {})
        
        if vehicle_type:
            # Check for required attributes
            required_attrs = vehicle_type.attributes.filter(is_required=True)
            missing_attrs = []
            
            for attr in required_attrs:
                if attr.slug not in specifications:
                    missing_attrs.append(attr.name)
            
            if missing_attrs:
                raise serializers.ValidationError({
                    "specifications": f"Missing required attributes for {vehicle_type.vehicle_type}: {', '.join(missing_attrs)}"
                })
        
        # Validate Make/Model/VehicleType consistency
        make = data.get('make')
        model = data.get('model')
        
        if make and model:
            if model.make != make:
                raise serializers.ValidationError({
                    "model": f"Model '{model.model}' does not belong to make '{make.make}'."
                })
        
        if vehicle_type and make:
            # Check if make supports this vehicle type
            if not make.vehicle_types.filter(id=vehicle_type.id).exists():
                 raise serializers.ValidationError({
                    "make": f"Make '{make.make}' does not produce vehicles of type '{vehicle_type.vehicle_type}'."
                })

        if vehicle_type and model:
             # Check if model belongs to this vehicle type
             # Note: model.vehicle_type is nullable, but if set, it must match
             if model.vehicle_type and model.vehicle_type != vehicle_type:
                 raise serializers.ValidationError({
                    "model": f"Model '{model.model}' is defined as '{model.vehicle_type.vehicle_type}', not '{vehicle_type.vehicle_type}'."
                })

        # Validate Business Ownership
        business = data.get('business')
        user = self.context['request'].user
        
        if business and business.owner != user:
            raise serializers.ValidationError({
                "business": "You can only list a vehicle under a business you own."
            })
            
        return data
    
    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.saved_by.filter(user=user).exists()
        return False




class SellerProfileSerializer(serializers.ModelSerializer):
    seller_type_name = serializers.CharField(source='seller_type.seller_type', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'business', 'business_name', 'seller_type', 'seller_type_name'
        ]


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = ['id', 'user', 'subscription_preferences', 'notification_settings']
        read_only_fields = ['user']


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ['id', 'user', 'name', 'query_params', 'notification_enabled', 'created_at']
        read_only_fields = ['user', 'created_at']


# REPLACED: SellerReviewSerializer is now BusinessReviewSerializer
class SavedVehicleSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    
    class Meta:
        model = SavedVehicle
        fields = ['id', 'vehicle', 'vehicle_details', 'created_at']
        read_only_fields = ['created_at']
