from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from business.models import BusinessProfile

class Property(models.Model):
    class ListingType(models.TextChoices):
        SALE = 'SALE', _('For Sale')
        RENT = 'RENT', _('To Rent')

    class PropertyType(models.TextChoices):
        DOMESTIC = 'DOMESTIC', _('Domestic')
        COMMERCIAL = 'COMMERCIAL', _('Commercial')

    class Category(models.TextChoices):
        # Domestic
        HOUSE = 'HOUSE', _('House')
        APARTMENT = 'APARTMENT', _('Apartment')
        BUNGALOW = 'BUNGALOW', _('Bungalow')
        LAND = 'LAND', _('Land')
        # Commercial
        OFFICE = 'OFFICE', _('Office')
        RETAIL = 'RETAIL', _('Retail')
        INDUSTRIAL = 'INDUSTRIAL', _('Industrial')
        HOSPITALITY = 'HOSPITALITY', _('Hospitality')
        OTHER = 'OTHER', _('Other')

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', _('Available')
        UNDER_OFFER = 'UNDER_OFFER', _('Under Offer')
        SOLD = 'SOLD', _('Sold')
        LET = 'LET', _('Let')

    # Ownership
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='properties')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='listed_properties')

    # Core details
    title = models.CharField(max_length=200)
    description = models.TextField()
    listing_type = models.CharField(max_length=10, choices=ListingType.choices, default=ListingType.SALE)
    property_type = models.CharField(max_length=15, choices=PropertyType.choices, default=PropertyType.DOMESTIC)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.HOUSE)
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    price_qualifier = models.CharField(max_length=50, blank=True, help_text="e.g. Guide Price, OIEO")

    # Specs
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    area_sqft = models.PositiveIntegerField(null=True, blank=True)
    
    # Location
    location = models.CharField(max_length=255, help_text="Full address or area name")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    features = models.JSONField(default=list, blank=True, help_text="List of feature strings")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.listing_type})"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_primary:
            PropertyImage.objects.filter(property=self.property, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.property.title}"


class SavedProperty(models.Model):
    """User favorites"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'property']

    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class PropertySavedSearch(models.Model):
    """User saved searches for notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_saved_searches')
    name = models.CharField(max_length=100)
    query_params = models.JSONField(help_text="Search filters in JSON format")
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"
