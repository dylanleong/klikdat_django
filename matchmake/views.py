from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
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

class DiscoveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchmakeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'matchmake_profile', None)
        
        # Exclude self and already swiped users
        swiped_ids = Swipe.objects.filter(swiper=user).values_list('swiped_id', flat=True)
        queryset = MatchmakeProfile.objects.exclude(user=user).exclude(user_id__in=swiped_ids)
        
        # Filters from query parameters
        gender = self.request.query_params.get('gender')
        min_age = self.request.query_params.get('min_age')
        max_age = self.request.query_params.get('max_age')
        interest_ids = self.request.query_params.getlist('interests')

        if gender and gender != 'Everyone':
            queryset = queryset.filter(user__profile__gender=gender)
        elif profile and profile.pref_looking_for != 'Everyone':
            queryset = queryset.filter(user__profile__gender=profile.pref_looking_for)
            
        # Age filtering
        from datetime import date
        today = date.today()
        
        if min_age:
            try:
                min_age = int(min_age)
                max_dob = date(today.year - min_age, today.month, today.day)
                queryset = queryset.filter(user__profile__dob__lte=max_dob)
            except (ValueError, TypeError):
                pass
        
        if max_age:
            try:
                max_age = int(max_age)
                min_dob = date(today.year - max_age - 1, today.month, today.day)
                queryset = queryset.filter(user__profile__dob__gt=min_dob)
            except (ValueError, TypeError):
                pass

        if interest_ids:
            queryset = queryset.filter(interests__id__in=interest_ids).distinct()
            
        return queryset

    @action(detail=False, methods=['post'])
    def reset(self, request):
        Swipe.objects.filter(swiper=request.user).delete()
        return Response({'status': 'swipes reset'})

class SwipeViewSet(viewsets.ModelViewSet):
    serializer_class = SwipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Swipe.objects.filter(swiper=self.request.user)

    def perform_create(self, serializer):
        swipe = serializer.save(swiper=self.request.user)
        
        # Check for matching swipe
        if swipe.is_like:
            matching_swipe = Swipe.objects.filter(
                swiper=swipe.swiped,
                swiped=self.request.user,
                is_like=True
            ).first()
            
            if matching_swipe:
                # CREATED A MATCH!
                match, created = Match.objects.get_or_create(
                    user1=min(self.request.user, swipe.swiped, key=lambda u: u.id),
                    user2=max(self.request.user, swipe.swiped, key=lambda u: u.id)
                )
                
                if created:
                    # Create a ChatRoom
                    room = ChatRoom.objects.create(name=f'Match: {self.request.user.username} & {swipe.swiped.username}')
                    room.participants.add(self.request.user, swipe.swiped)
                    match.chat_room = room
                    match.save()

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
