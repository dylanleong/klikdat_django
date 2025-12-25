from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import MatchmakeProfile

@receiver(post_save, sender=User)
def create_matchmake_profile(sender, instance, created, **kwargs):
    if created:
        MatchmakeProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_matchmake_profile(sender, instance, **kwargs):
    if hasattr(instance, 'matchmake_profile'):
        instance.matchmake_profile.save()
