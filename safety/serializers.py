from rest_framework import serializers
from .models import SafetyCircle, SafetyCircleMember
from django.contrib.auth import get_user_model
from locations.models import Location
from locations.serializers import LocationSerializer

User = get_user_model()

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class SafetyCircleMemberSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    latest_location = serializers.SerializerMethodField(read_only=True)
    geoklik_id = serializers.SerializerMethodField(read_only=True)
    precise_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SafetyCircleMember
        fields = ['id', 'user', 'is_admin', 'joined_at', 'latest_location', 'geoklik_id', 'precise_id']

    def get_latest_location(self, obj):
        location = Location.objects.filter(user=obj.user).order_by('-timestamp').first()
        if location:
            return LocationSerializer(location).data
        
        # Fallback to Profile data (IP-based or manual)
        profile = getattr(obj.user, 'profile', None)
        if profile and profile.latitude and profile.longitude:
            return {
                'id': None,
                'user': obj.user.id,
                'latitude': profile.latitude,
                'longitude': profile.longitude,
                'timestamp': profile.last_active or obj.joined_at,
                'device_id': 'profile-fallback'
            }
        return None

    def get_geoklik_id(self, obj):
        from geo.utils import GeoKlikService
        
        # Try latest location first
        location = Location.objects.filter(user=obj.user).order_by('-timestamp').first()
        if location:
            result = GeoKlikService.encode(float(location.latitude), float(location.longitude))
            return result.get('geoklik_id')
        
        # Fallback to Profile coords
        profile = getattr(obj.user, 'profile', None)
        if profile and profile.latitude and profile.longitude:
            result = GeoKlikService.encode(float(profile.latitude), float(profile.longitude))
            return result.get('geoklik_id')
            
        return None

    def get_precise_id(self, obj):
        from geo.utils import GeoKlikService
        
        # Try latest location first
        location = Location.objects.filter(user=obj.user).order_by('-timestamp').first()
        if location:
            result = GeoKlikService.encode(float(location.latitude), float(location.longitude))
            return result.get('precise_id')
        
        # Fallback to Profile coords
        profile = getattr(obj.user, 'profile', None)
        if profile and profile.latitude and profile.longitude:
            result = GeoKlikService.encode(float(profile.latitude), float(profile.longitude))
            return result.get('precise_id')
            
        return None

class SafetyCircleSerializer(serializers.ModelSerializer):
    owner = UserShortSerializer(read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = SafetyCircle
        fields = ['id', 'name', 'invite_code', 'owner', 'created_at', 'member_count']
        read_only_fields = ['invite_code', 'owner']
