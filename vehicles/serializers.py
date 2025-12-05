from rest_framework import serializers
from .models import (
    VehicleType, Make, Model, Gearbox, BodyType, 
    Color, FuelType, SellerType, Vehicle, VehicleImage, Favorite
)


class VehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImage
        fields = ['id', 'image', 'is_primary', 'created_at']


class FavoriteSerializer(serializers.ModelSerializer):
    vehicle_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Favorite
        fields = ['id', 'vehicle', 'vehicle_details', 'created_at']
        read_only_fields = ['created_at']
        
    def get_vehicle_details(self, obj):
        # Return basic vehicle info for display
        return {
            'id': obj.vehicle.id,
            'year': obj.vehicle.year,
            'make': obj.vehicle.make.make,
            'model': obj.vehicle.model.model,
            'price': obj.vehicle.price,
            'image': obj.vehicle.images.filter(is_primary=True).first().image.url if obj.vehicle.images.filter(is_primary=True).exists() else None
        }


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'vehicle_type']


class MakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Make
        fields = ['id', 'make']


class ModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.make', read_only=True)
    
    class Meta:
        model = Model
        fields = ['id', 'model', 'make', 'make_name']


class GearboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gearbox
        fields = ['id', 'gearbox']


class BodyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyType
        fields = ['id', 'body_type']


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'color']


class FuelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelType
        fields = ['id', 'fuel_type']


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
    gearbox_name = serializers.CharField(source='gearbox.gearbox', read_only=True)
    body_type_name = serializers.CharField(source='body_type.body_type', read_only=True)
    color_name = serializers.CharField(source='color.color', read_only=True)
    fuel_type_name = serializers.CharField(source='fuel_type.fuel_type', read_only=True)
    seller_type_name = serializers.CharField(source='seller_type.seller_type', read_only=True)
    images = VehicleImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'owner_username',
            'vehicle_type', 'vehicle_type_name',
            'make', 'make_name',
            'model', 'model_name',
            'gearbox', 'gearbox_name',
            'body_type', 'body_type_name',
            'color', 'color_name',
            'fuel_type', 'fuel_type_name',
            'seller_type', 'seller_type_name',
            'price', 'year', 'mileage', 'location',
            'num_doors', 'num_seats',
            'battery_range', 'charging_time',
            'engine_size', 'engine_power', 'acceleration', 'fuel_consumption',
            'created_at', 'updated_at',
            'images', 'is_favorited'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']
    
    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False
    
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
