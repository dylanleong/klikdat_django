from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile, VerificationProfile, Notification

class ProfileSerializer(serializers.ModelSerializer):
    # Use higher precision for input to avoid validation errors, then round in validate()
    latitude = serializers.DecimalField(max_digits=15, decimal_places=10, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=15, decimal_places=10, required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ['gender', 'dob', 'phone', 'recovery_email', 'avatar', 'ip_address', 'ip_country', 'latitude', 'longitude', 
                  'address_line_1', 'address_line_2', 'city', 'state', 'postcode', 'country']

    def validate_latitude(self, value):
        return round(value, 6) if value is not None else None

    def validate_longitude(self, value):
        return round(value, 6) if value is not None else None

class VerificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationProfile
        fields = ['v1_email', 'v2_phone', 'v3_location', 'v4_gender', 'v5_age', 
                  'verification_video', 'detected_gender', 'detected_age_range', 'ai_analysis_status', 'ai_analysis_message', 'level']
        read_only_fields = ['detected_gender', 'detected_age_range', 'ai_analysis_status', 'ai_analysis_message', 'level']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    verification_profile = VerificationProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile', 'verification_profile']
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        verification_data = validated_data.pop('verification_profile', None)
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        # Profile creation is handled by signal, but we update it if data is provided
        if profile_data and hasattr(user, 'profile'):
            self.update_related(user.profile, profile_data)
        
        if verification_data and hasattr(user, 'verification_profile'):
            self.update_related(user.verification_profile, verification_data)
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        verification_data = validated_data.pop('verification_profile', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()

        if profile_data:
            if not hasattr(instance, 'profile'):
                 Profile.objects.create(user=instance)
            self.update_related(instance.profile, profile_data)

        if verification_data:
            if not hasattr(instance, 'verification_profile'):
                 VerificationProfile.objects.create(user=instance)
            self.update_related(instance.verification_profile, verification_data)

        return instance
    
    def update_related(self, instance, data):
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
