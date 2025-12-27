from django.contrib.auth.models import User
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import MatchmakeProfile, Interest, MatchmakePhoto, Swipe, Match
from .serializers import (
    MatchmakeProfileSerializer, InterestSerializer, MatchmakePhotoSerializer,
    SwipeSerializer, MatchSerializer
)
from chat.models import ChatRoom

class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [permissions.IsAuthenticated]

class MatchmakeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MatchmakeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MatchmakeProfile.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        # Ensure profile exists for the current user
        if request.user.is_authenticated:
            MatchmakeProfile.objects.get_or_create(user=request.user)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='public/(?P<user_id>\d+)')
    def public_profile(self, request, user_id=None):
        """Retrieve a specific user's public profile by their User ID."""
        profile = get_object_or_404(MatchmakeProfile, user_id=user_id)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

class DiscoveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchmakeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'matchmake_profile', None)
        
        # Update last active
        if hasattr(user, 'profile'):
            user.profile.update_last_active()

        # Exclude self and already swiped users
        swiped_ids = Swipe.objects.filter(swiper=user).values_list('swiped_id', flat=True)
        queryset = MatchmakeProfile.objects.exclude(user=user).exclude(user_id__in=swiped_ids)
        
        # Query parameters
        params = self.request.query_params
        
        # Basic Filters
        gender = params.get('gender')
        interest_ids = params.getlist('interests')
        intentions = params.getlist('intentions')
        height_min = params.get('height_min')
        height_max = params.get('height_max')
        ethnicity = params.get('ethnicity')
        education = params.get('education')
        languages = params.get('languages')
        religion = params.get('religion')
        politics = params.get('politics')
        family_plans = params.get('family_plans')
        zodiac = params.get('zodiac')
        verification_level = params.get('verification_level')
        completeness_min = params.get('completeness_min')
        active_status = params.get('active_status') # 'day', 'week', 'month'
        smoking = params.get('smoking')
        drinking = params.get('drinking')
        exercise = params.get('exercise')
        pets = params.get('pets')
        profession = params.get('profession')

        if gender and gender != 'Everyone':
            queryset = queryset.filter(user__profile__gender=gender)
        elif profile and profile.pref_looking_for != 'Everyone':
            queryset = queryset.filter(user__profile__gender=profile.pref_looking_for)
            
        # Age filtering
        from datetime import date, timedelta
        from django.utils import timezone
        today = date.today()
        
        min_age = params.get('min_age')
        max_age = params.get('max_age')
        if min_age:
            try:
                min_age = int(min_age)
                max_dob = date(today.year - min_age, today.month, today.day)
                queryset = queryset.filter(user__profile__dob__lte=max_dob)
            except (ValueError, TypeError): pass
        if max_age:
            try:
                max_age = int(max_age)
                min_dob = date(today.year - max_age - 1, today.month, today.day)
                queryset = queryset.filter(user__profile__dob__gt=min_dob)
            except (ValueError, TypeError): pass

        # Advanced Filters
        if intentions: queryset = queryset.filter(relationship_goal__in=intentions)
        if height_min: queryset = queryset.filter(height__gte=height_min)
        if height_max: queryset = queryset.filter(height__lte=height_max)
        if ethnicity: queryset = queryset.filter(ethnicity__icontains=ethnicity)
        if education: queryset = queryset.filter(education__icontains=education)
        if religion: queryset = queryset.filter(religion__icontains=religion)
        if politics: queryset = queryset.filter(politics__icontains=politics)
        if family_plans: queryset = queryset.filter(future_family_plans__icontains=family_plans)
        if zodiac: queryset = queryset.filter(zodiac__iexact=zodiac)
        if smoking: queryset = queryset.filter(smoking=smoking)
        if drinking: queryset = queryset.filter(drinking=drinking)
        if exercise: queryset = queryset.filter(exercise=exercise)
        if languages: queryset = queryset.filter(languages_spoken__icontains=languages)
        if pets: queryset = queryset.filter(pets__icontains=pets)
        if profession: queryset = queryset.filter(profession__icontains=profession)
        
        if interest_ids:
            queryset = queryset.filter(interests__id__in=interest_ids).distinct()

        # Verification Level
        if verification_level:
            try:
                v_level = int(verification_level)
                if v_level >= 2:
                    queryset = queryset.filter(user__verification_profile__v1_email=True, user__verification_profile__v2_phone=True)
                if v_level >= 3:
                     queryset = queryset.filter(user__verification_profile__v3_location=True)
                if v_level >= 4:
                     queryset = queryset.filter(user__verification_profile__v4_video=True)
            except: pass

        # Active Status
        if active_status:
            now = timezone.now()
            if active_status == 'day':
                queryset = queryset.filter(user__profile__last_active__gte=now - timedelta(days=1))
            elif active_status == 'week':
                queryset = queryset.filter(user__profile__last_active__gte=now - timedelta(weeks=1))
            elif active_status == 'month':
                queryset = queryset.filter(user__profile__last_active__gte=now - timedelta(days=30))

        # Distance Filtering
        max_dist = params.get('max_distance') or (profile.pref_max_distance if profile else None)
        if max_dist and hasattr(user, 'profile') and user.profile.latitude and user.profile.longitude:
            try:
                max_dist = float(max_dist)
                lat = float(user.profile.latitude)
                lng = float(user.profile.longitude)
                deg_lat = max_dist / 111.1
                deg_lng = max_dist / (111.1 * 0.7)
                queryset = queryset.filter(
                    Q(
                        user__profile__latitude__range=(lat - deg_lat, lat + deg_lat),
                        user__profile__longitude__range=(lng - deg_lng, lng + deg_lng)
                    ) | Q(user__profile__latitude__isnull=True)
                )
            except: pass

        # Sorting (handle multiple)
        sort_params = params.getlist('sort_by')
        if not sort_params:
            sort_params = [params.get('sort_by', 'recent')]
            
        ordering = []
        for s in sort_params:
            if s == 'recent':
                ordering.append('-user__profile__last_active')
            elif s == 'age_asc':
                ordering.append('-user__profile__dob')
            elif s == 'age_desc':
                ordering.append('user__profile__dob')
            elif s == 'distance' and hasattr(user, 'profile') and user.profile.latitude and user.profile.longitude:
                from django.db.models import F
                from django.db.models.functions import Abs
                queryset = queryset.annotate(
                    dist_approx=Abs(F('user__profile__latitude') - user.profile.latitude) + 
                                Abs(F('user__profile__longitude') - user.profile.longitude)
                )
                ordering.append('dist_approx')
                # Note: This is an approximation. 
                # If we have PostGIS, we'd use:
                # from django.contrib.gis.db.models.functions import Distance
                # ref_point = Point(float(user.profile.longitude), float(user.profile.latitude), srid=4326)
                # queryset = queryset.annotate(dist=Distance('user__profile__location', ref_point)).order_by('dist')
                
        if ordering:
            queryset = queryset.order_by(*ordering)
            
        return queryset

    @action(detail=False, methods=['post'])
    def reset(self, request):
        # Only delete swipes where is_like=False to avoid removing matches or showing matched users again
        Swipe.objects.filter(swiper=request.user, is_like=False).delete()
        return Response({'status': 'swipes reset (passes only)'})

class SwipeViewSet(viewsets.ModelViewSet):
    serializer_class = SwipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Swipe.objects.filter(swiper=self.request.user)

    def create(self, request, *args, **kwargs):
        swiped_id = request.data.get('swiped')
        is_like = request.data.get('is_like') == True
        
        if not swiped_id:
            return Response({'error': 'swiped user id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use update_or_create directly in the view for absolute reliability
        swipe, created = Swipe.objects.update_or_create(
            swiper=request.user,
            swiped_id=swiped_id,
            defaults={'is_like': is_like}
        )
        
        serializer = self.get_serializer(swipe)
        response_data = serializer.data
        
        # Check for matching swipe
        if is_like:
            matching_swipe = Swipe.objects.filter(
                swiper_id=swiped_id,
                swiped=request.user,
                is_like=True
            ).first()
            
            if matching_swipe:
                # CREATED A MATCH!
                match, m_created = Match.objects.get_or_create(
                    user1_id=min(request.user.id, int(swiped_id)),
                    user2_id=max(request.user.id, int(swiped_id))
                )
                
                if not match.chat_room:
                    # Create a ChatRoom
                    swiped_user = User.objects.get(id=swiped_id)
                    room = ChatRoom.objects.create(
                        name=f'Match: {request.user.username} & {swiped_user.username}',
                        module='matchmake'
                    )
                    room.participants.add(request.user, swiped_user)
                    match.chat_room = room
                    match.save()
                    
                    # Create Notifications
                    from users.models import Notification
                    Notification.objects.create(
                        user=request.user,
                        type='match',
                        title='New Match!',
                        body=f'You matched with {swiped_user.username}!',
                        data={'chat_room_id': room.id}
                    )
                    Notification.objects.create(
                        user=swiped_user,
                        type='match',
                        title='New Match!',
                        body=f'You matched with {request.user.username}!',
                        data={'chat_room_id': room.id}
                    )
                
                if match.chat_room:
                    response_data['chat_room'] = match.chat_room.id
                    response_data['match_id'] = match.id
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def liked(self, request):
        """Returns users the current user has liked."""
        swipes = Swipe.objects.filter(swiper=request.user, is_like=True)
        # Get profiles of swiped users
        swiped_user_ids = swipes.values_list('swiped_id', flat=True)
        profiles = MatchmakeProfile.objects.filter(user_id__in=swiped_user_ids)
        serializer = MatchmakeProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def liked_me(self, request):
        """Returns users who have liked the current user but aren't matched yet."""
        # Swipes where current user is the 'swiped' and is_like=True
        liked_me_swipes = Swipe.objects.filter(swiped=request.user, is_like=True)
        
        # Exclude users already matched with current user
        matched_user_ids = Match.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        ).values_list('user1_id', 'user2_id')
        
        # Flatten and remove requester's own ID
        matched_ids = set()
        for u1, u2 in matched_user_ids:
            matched_ids.add(u1)
            matched_ids.add(u2)
        matched_ids.discard(request.user.id)
        
        swiper_ids = liked_me_swipes.exclude(swiper_id__in=matched_ids).values_list('swiper_id', flat=True)
        profiles = MatchmakeProfile.objects.filter(user_id__in=swiper_ids)
        serializer = MatchmakeProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def unlike(self, request):
        """Unlikes a user, removes match and chat room."""
        target_id = request.data.get('swiped')
        if not target_id:
            return Response({'error': 'swiped user id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update Swipe to False (unlike)
        # This keeps the swipe record but marks it as a dislike
        # which triggers the "heartbreak" status for the other user
        Swipe.objects.update_or_create(
            swiper=request.user,
            swiped_id=target_id,
            defaults={'is_like': False}
        )
        
        # Find and delete match and chat room
        match = Match.objects.filter(
            Q(user1=request.user, user2_id=target_id) |
            Q(user1_id=target_id, user2=request.user)
        ).first()
        
        if match:
            if match.chat_room:
                match.chat_room.delete()
            match.delete()
            
        return Response({'status': 'unliked and unmatched successfully'})

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Match.objects.filter(Q(user1=self.request.user) | Q(user2=self.request.user))

class MatchmakePhotoViewSet(viewsets.ModelViewSet):
    serializer_class = MatchmakePhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow users to manage their own photos
        return MatchmakePhoto.objects.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        # Automatically link to the user's MatchmakeProfile
        profile = getattr(self.request.user, 'matchmake_profile', None)
        if not profile:
            # Create profile if it doesn't exist (though usually it should)
            profile = MatchmakeProfile.objects.create(user=self.request.user)
        serializer.save(profile=profile)
