from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, VerificationProfileSerializer
from .models import VerificationProfile
import random
import string
from django_q.tasks import async_task

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=user.id)

class VerificationViewSet(viewsets.GenericViewSet):
    queryset = VerificationProfile.objects.all()
    serializer_class = VerificationProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return VerificationProfile.objects.get_or_create(user=self.request.user)[0]

    @action(detail=False, methods=['get'])
    def status(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def request_v2_code(self, request):
        """Generate a 6-digit code for WhatsApp verification"""
        instance = self.get_object()
        code = ''.join(random.choices(string.digits, k=6))
        instance.v2_code = code
        instance.save()
        return Response({'code': code})

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def v2_webhook(self, request):
        """
        Simulated WhatsApp webhook. 
        Expects: {'code': '123456', 'phone': '...'}
        In a real scenario, the phone would be matched against the user's phone.
        """
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile = VerificationProfile.objects.filter(v2_code=code).first()
        if profile:
            profile.v2_phone = True
            profile.v2_code = None # Clear after use
            profile.save()
            return Response({'message': 'Phone verified successfully'})
        
        return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_geo(self, request):
        """V3: Trigger GeoIP check based on Middleware-detected country vs Flutter-provided country"""
        profile = self.get_object()
        flutter_country_code = request.data.get('country_code') # From geolocator
        
        # In a real scenario, we compare request.META['GEOIP_COUNTRY'] (set by middleware)
        # with flutter_country_code. 
        # For now, we'll mark as verified if they match or if provided.
        # Middleware will be implemented separately.
        
        if flutter_country_code:
            # Also capture coordinates if provided
            lat = request.data.get('latitude')
            lng = request.data.get('longitude')
            if lat and lng:
                profile.user.profile.latitude = lat
                profile.user.profile.longitude = lng
                profile.user.profile.save() # This triggers the save_location_history signal
            
            profile.v3_location = True
            profile.save()
            return Response({'message': 'Location verified and logged'})
        
        return Response({'error': 'Country code required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def upload_video(self, request):
        """V4/V5: Upload video and trigger AI analysis"""
        profile = self.get_object()
        video = request.FILES.get('video')
        if not video:
            return Response({'error': 'Video file required'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.verification_video = video
        profile.ai_analysis_status = 'processing'
        profile.save()
        
        # Trigger background task
        async_task('users.tasks.analyze_verification_video', profile.id)
        
        return Response({'message': 'Video uploaded. AI analysis started.', 'status': 'processing'})
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset all verification statuses for testing"""
        profile = self.get_object()
        profile.v1_email = False
        profile.v2_phone = False
        profile.v3_location = False
        profile.v4_gender = False
        profile.v5_age = False
        profile.v2_code = None
        profile.verification_video = None
        profile.detected_gender = None
        profile.detected_age_range = None
        profile.ai_analysis_status = 'pending'
        profile.save()
        return Response({'message': 'Verification status reset'})
