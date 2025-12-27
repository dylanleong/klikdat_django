from rest_framework import serializers
from .models import Location

class LocationSerializer(serializers.ModelSerializer):
    # Use higher precision for input to avoid validation errors, then round in validate()
    latitude = serializers.DecimalField(max_digits=15, decimal_places=10)
    longitude = serializers.DecimalField(max_digits=15, decimal_places=10)

    class Meta:
        model = Location
        fields = ['id', 'user', 'latitude', 'longitude', 'timestamp', 'device_id']
        read_only_fields = ['user', 'timestamp']

    def validate_latitude(self, value):
        return round(value, 6)

    def validate_longitude(self, value):
        return round(value, 6)

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
