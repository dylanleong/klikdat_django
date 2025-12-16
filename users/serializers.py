from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='profile.avatar', required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'is_superuser', 'avatar']
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        avatar = validated_data.pop('profile', {}).get('avatar')
        
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        if avatar:
            if hasattr(user, 'profile'):
                user.profile.avatar = avatar
                user.profile.save()
            else:
                # Should be created by signal, but safe fallback
                from .models import Profile
                Profile.objects.create(user=user, avatar=avatar)
                
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        avatar = validated_data.pop('profile', {}).get('avatar')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()
        
        if avatar:
             if hasattr(instance, 'profile'):
                instance.profile.avatar = avatar
                instance.profile.save()
             else:
                from .models import Profile
                Profile.objects.create(user=instance, avatar=avatar)
                
        return instance
