from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, VerificationProfileSerializer, NotificationSerializer
from .models import VerificationProfile, Notification
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
                profile.user.profile.latitude = round(float(lat), 6)
                profile.user.profile.longitude = round(float(lng), 6)
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

    @action(detail=False, methods=['post'])
    def resend_email(self, request):
        """Resend verification email for V1"""
        from allauth.account.models import EmailAddress
        from allauth.account.utils import send_email_confirmation
        
        user = request.user
        if not user.email:
            return Response({'error': 'User has no email address'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if already verified
        try:
            email_obj = EmailAddress.objects.get(user=user, email=user.email)
            if email_obj.verified:
                # Ensure profile is synced
                if hasattr(user, 'verification_profile') and not user.verification_profile.v1_email:
                    user.verification_profile.v1_email = True
                    user.verification_profile.save()
                return Response({'message': 'Email is already verified'})
        except EmailAddress.DoesNotExist:
            # Should exist if created via RegisterView, but handle just in case
            pass

        # Send confirmation
        send_email_confirmation(request, user)
        return Response({'message': 'Verification email sent. Check your console logs.'})

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'ok'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})
