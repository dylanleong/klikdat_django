from rest_framework import serializers
from .models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'user', 'latitude', 'longitude', 'timestamp', 'device_id']
        read_only_fields = ['user', 'timestamp']

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
