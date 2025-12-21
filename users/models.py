from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    phone = models.CharField(max_length=20, blank=True, null=True)
    recovery_email = models.EmailField(blank=True, null=True)
    
    # IP and Geolocation
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ip_country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

class VerificationProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_profile')
    v1_email = models.BooleanField(default=False)
    v2_phone = models.BooleanField(default=False)
    v3_location = models.BooleanField(default=False)
    v4_gender = models.BooleanField(default=False)
    v5_age = models.BooleanField(default=False)
    
    verification_video = models.FileField(upload_to='verification_videos/', null=True, blank=True)
    v2_code = models.CharField(max_length=6, null=True, blank=True) # Unique 6-digit code for WhatsApp
    
    # AI Analysis Results
    detected_gender = models.CharField(max_length=20, null=True, blank=True)
    detected_age_range = models.CharField(max_length=20, null=True, blank=True)
    ai_analysis_status = models.CharField(max_length=20, default='pending') # pending, processing, completed, failed

    def __str__(self):
        return f"{self.user.username}'s Verification Status"

    @property
    def level(self):
        levels = [self.v1_email, self.v2_phone, self.v3_location, self.v4_gender, self.v5_age]
        return sum(1 for v in levels if v)
