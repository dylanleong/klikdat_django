from django.db import models
from django.contrib.auth.models import User

class BusinessProfile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_profiles')
    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False, help_text='True if this is a default profile for a private individual')
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    about_us = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.name}'

class BusinessReview(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_reviews_given')
    module = models.CharField(max_length=50)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['business', 'reviewer', 'module']
        ordering = ['-created_at']
