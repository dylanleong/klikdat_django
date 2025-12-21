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

class MatchmakeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MatchmakeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MatchmakeProfile.objects.filter(user=self.request.user)

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
        
        if profile:
            # Basic filters
            if profile.pref_looking_for != 'Everyone':
                queryset = queryset.filter(user__profile__gender=profile.pref_looking_for)
            
            # Age filter would go here (requires calculation in DB or filtering here)
            # Distance filter would go here (requires PostGIS)
            
        return queryset

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
