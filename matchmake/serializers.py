from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MatchmakeProfile, Interest, MatchmakePhoto, Swipe, Match

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = '__all__'

class MatchmakePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchmakePhoto
        fields = ('id', 'image', 'is_primary', 'created_at')

class MatchmakeProfileSerializer(serializers.ModelSerializer):
    photos = MatchmakePhotoSerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Interest.objects.all(), write_only=True, source='interests'
    )
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = MatchmakeProfile
        fields = (
            'id', 'bio', 'intro_video', 'smoking', 'drinking', 'exercise', 
            'dietary_preferences', 'education', 'profession', 
            'relationship_goal', 'interests', 'interest_ids', 
            'pref_min_age', 'pref_max_age', 'pref_max_distance', 
            'pref_looking_for', 'photos', 'user_details'
        )

    def get_user_details(self, obj):
        return {
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'gender': obj.user.profile.gender if hasattr(obj.user, 'profile') else None,
            'age': self._calculate_age(obj.user.profile.dob) if hasattr(obj.user, 'profile') and obj.user.profile.dob else None,
            'avatar': obj.user.profile.avatar.url if hasattr(obj.user, 'profile') and obj.user.profile.avatar else None,
        }

    def _calculate_age(self, dob):
        from datetime import date
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

class SwipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swipe
        fields = ('id', 'swiped', 'is_like', 'created_at')
        read_only_fields = ('swiper',)

    def create(self, validated_data):
        validated_data['swiper'] = self.context['request'].user
        return super().create(validated_data)

class MatchSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ('id', 'chat_room', 'created_at', 'other_user')

    def get_other_user(self, obj):
        request = self.context.get('request')
        user = request.user
        other = obj.user2 if obj.user1 == user else obj.user1
        return {
            'id': other.id,
            'username': other.username,
            'avatar': other.profile.avatar.url if hasattr(other, 'profile') and other.profile.avatar else None,
        }
