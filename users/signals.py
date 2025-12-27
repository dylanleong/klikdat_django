from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, VerificationProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        VerificationProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if profile exists before saving (in case it was deleted or legacy user)
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)

    if hasattr(instance, 'verification_profile'):
        instance.verification_profile.save()
    else:
        VerificationProfile.objects.create(user=instance)

from django.contrib.auth.signals import user_logged_in
from geo.models import IpAsn, CountryInfo
from locations.models import Location

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(pre_save, sender=Profile)
def profile_pre_save(sender, instance, **kwargs):
    """
    Automatically populate ip_country from ip_address using IpAsn and CountryInfo.
    """
    if instance.ip_address:
        # Check if ip_address has changed or ip_country is empty
        update_country = False
        if not instance.pk:
            update_country = True
        else:
            try:
                old_instance = Profile.objects.get(pk=instance.pk)
                # Update if IP changed, OR if country is empty, OR if country is not a 2-char code
                if (old_instance.ip_address != instance.ip_address or 
                    not instance.ip_country or 
                    len(instance.ip_country) != 2):
                    update_country = True
            except Profile.DoesNotExist:
                update_country = True

        if update_country:
            try:
                ip_asn = IpAsn.objects.filter(start_ip__lte=instance.ip_address, end_ip__gte=instance.ip_address).first()
                if ip_asn:
                    instance.ip_country = ip_asn.country_code
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error looking up IP info for profile {instance.id}: {e}")

@receiver(post_save, sender=Profile)
def save_location_history(sender, instance, **kwargs):
    """
    Log geolocation changes to Location history.
    """
    if instance.latitude and instance.longitude:
        # Avoid creating duplicate history if nothing changed significantly
        last_history = Location.objects.filter(user=instance.user).order_by('-timestamp').first()
        if last_history:
            # Check if coordinates changed since last log
            if (last_history.latitude != instance.latitude or 
                last_history.longitude != instance.longitude):
                Location.objects.create(
                    user=instance.user,
                    latitude=instance.latitude,
                    longitude=instance.longitude
                )
        else:
            # First location record
            Location.objects.create(
                user=instance.user,
                latitude=instance.latitude,
                longitude=instance.longitude
            )

@receiver(user_logged_in)
def update_user_ip_info(sender, user, request, **kwargs):
    ip = get_client_ip(request)
    if ip:
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.ip_address = ip
            # Country lookup is now handled by profile_pre_save
            profile.save()

from allauth.account.signals import email_confirmed

@receiver(email_confirmed)
def update_user_email_verification(request, email_address, **kwargs):
    user = email_address.user
    if hasattr(user, 'verification_profile'):
        user.verification_profile.v1_email = True
        user.verification_profile.save()
