
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Vehicle, VehicleProfile, SellerType, VehicleImage
import os

@receiver(post_delete, sender=VehicleImage)
def cleanup_vehicle_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(post_save, sender=Vehicle)
def ensure_vehicle_profile_and_seller_type(sender, instance, created, **kwargs):
    if created and instance.owner:
        # Get or create profile for the owner
        profile, _ = VehicleProfile.objects.get_or_create(
            user=instance.owner,
            defaults={'seller_type': SellerType.objects.get_or_create(seller_type='Private')[0]}
        )
        
        # If seller_type is not set on the vehicle, set it derived from profile
        if not instance.seller_type:
            instance.seller_type = profile.seller_type
            instance.save(update_fields=['seller_type'])
