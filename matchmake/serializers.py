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
    relationship_status = serializers.SerializerMethodField()

    class Meta:
        model = MatchmakeProfile
        fields = (
            'id', 'bio', 'intro_video', 'smoking', 'drinking', 'exercise', 
            'dietary_preferences', 'education', 'profession', 
            'relationship_goal', 'interests', 'interest_ids', 
            'height', 'ethnicity', 'languages_spoken', 'pets',
            'religion', 'politics', 'future_family_plans', 'zodiac',
            'pref_min_age', 'pref_max_age', 'pref_max_distance', 
            'pref_looking_for', 'photos', 'user_details', 'profile_completeness',
            'relationship_status'
        )

    def get_relationship_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return 'none'
        
        # My swipe for them
        my_swipe = Swipe.objects.filter(swiper=request.user, swiped=obj.user).first()
        if not my_swipe:
            return 'none'
        
        # Their swipe for me
        their_swipe = Swipe.objects.filter(swiper=obj.user, swiped=request.user).first()
        
        if my_swipe.is_like:
            if their_swipe:
                if their_swipe.is_like:
                    return 'matched'
                else:
                    return 'heartbreak' # They unliked or swiped left
            return 'liked'
        
        return 'disliked'

    def get_user_details(self, obj):
        request = self.context.get('request')
        current_user = request.user if request else None
        
        distance = None
        if current_user and hasattr(current_user, 'profile') and hasattr(obj.user, 'profile'):
            if current_user.profile.latitude is not None and current_user.profile.longitude is not None and \
               obj.user.profile.latitude is not None and obj.user.profile.longitude is not None:
                try:
                    lat1, lon1 = float(current_user.profile.latitude), float(current_user.profile.longitude)
                    lat2, lon2 = float(obj.user.profile.latitude), float(obj.user.profile.longitude)
                    
                    # Haversine formula for more accurate distance
                    import math
                    R = 6371  # Earth radius in KM
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    distance = R * c
                except:
                    pass

        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'gender': obj.user.profile.gender if hasattr(obj.user, 'profile') else None,
            'age': self._calculate_age(obj.user.profile.dob) if hasattr(obj.user, 'profile') and obj.user.profile.dob else None,
            'dob': obj.user.profile.dob if hasattr(obj.user, 'profile') else None,
            'avatar': obj.user.profile.avatar.url if hasattr(obj.user, 'profile') and obj.user.profile.avatar else None,
            'verification_level': obj.user.verification_profile.level if hasattr(obj.user, 'verification_profile') else 0,
            'last_active': obj.user.profile.last_active if hasattr(obj.user, 'profile') else None,
            'distance': round(distance, 1) if distance is not None else None,
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

class MatchSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ('id', 'chat_room', 'created_at', 'other_user')

    def get_other_user(self, obj):
        request = self.context.get('request')
        user = request.user
        other = obj.user2 if obj.user1 == user else obj.user1
        
        distance = None
        if hasattr(user, 'profile') and hasattr(other, 'profile') and \
           user.profile.latitude is not None and user.profile.longitude is not None and \
           other.profile.latitude is not None and other.profile.longitude is not None:
            try:
                lat1, lon1 = float(user.profile.latitude), float(user.profile.longitude)
                lat2, lon2 = float(other.profile.latitude), float(other.profile.longitude)
                
                import math
                R = 6371
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance = R * c
            except:
                pass

        # Get photos
        photos = []
        if hasattr(other, 'matchmake_profile'):
             p_objs = MatchmakePhoto.objects.filter(profile=other.matchmake_profile)
             photos = MatchmakePhotoSerializer(p_objs, many=True).data

        return {
            'id': other.id,
            'username': other.username,
            'first_name': other.first_name,
            'last_name': other.last_name,
            'gender': other.profile.gender if hasattr(other, 'profile') else None,
            'age': MatchmakeProfileSerializer()._calculate_age(other.profile.dob) if hasattr(other, 'profile') and other.profile.dob else None,
            'avatar': other.profile.avatar.url if hasattr(other, 'profile') and other.profile.avatar else None,
            'distance': round(distance, 1) if distance is not None else None,
            'photos': photos
        }
