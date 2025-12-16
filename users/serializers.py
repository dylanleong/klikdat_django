from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['gender', 'dob', 'phone', 'recovery_email', 'avatar', 'ip_address', 'ip_country', 'latitude', 'longitude', 
                  'address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        # Profile creation is handled by signal, but we update it if data is provided
        if profile_data and hasattr(user, 'profile'):
            self.update_profile(user.profile, profile_data)
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()

        if profile_data:
            # Create profile if not exists (healing self)
            if not hasattr(instance, 'profile'):
                 Profile.objects.create(user=instance)
            self.update_profile(instance.profile, profile_data)

        return instance
    
    def update_profile(self, profile, profile_data):
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
