
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Vehicle, SellerProfile, BuyerProfile, SellerType, VehicleImage
from business.models import BusinessProfile
import os

@receiver(post_delete, sender=VehicleImage)
def cleanup_vehicle_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            try:
                os.remove(instance.image.path)
            except (PermissionError, OSError):
                # Script might not have permissions (e.g. running outside Docker)
                # or file might be locked. We skip to avoid crashing the whole process.
                pass

@receiver(post_save, sender=Vehicle)
def ensure_seller_profile_and_seller_type(sender, instance, created, **kwargs):
    if created and instance.business:
        # Get or create seller profile for the business
        profile, _ = SellerProfile.objects.get_or_create(
            business=instance.business,
            defaults={'seller_type': SellerType.objects.get_or_create(seller_type='Private')[0]}
        )
        
        # If seller_type is not set on the vehicle, set it derived from profile
        if not instance.seller_type:
            instance.seller_type = profile.seller_type
            instance.save(update_fields=['seller_type'])


@receiver(post_save, sender=User)
def create_buyer_profile(sender, instance, created, **kwargs):
    if created:
        # Ensure BuyerProfile is created for all new users
        BuyerProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=BusinessProfile)
def create_seller_profile(sender, instance, created, **kwargs):
    if created:
        # Ensure SellerProfile is created for all new business profiles
        SellerProfile.objects.get_or_create(
            business=instance,
            defaults={'seller_type': SellerType.objects.get_or_create(seller_type='Private')[0]}
        )
