from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import BusinessProfile

@receiver(post_save, sender=User)
def create_default_business_profile(sender, instance, created, **kwargs):
    if created:
        BusinessProfile.objects.create(
            owner=instance,
            name=f"Private Profile ({instance.username})",
            is_private=True
        )
