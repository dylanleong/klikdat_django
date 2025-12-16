from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if profile exists before saving (in case it was deleted or legacy user)
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)

from django.contrib.auth.signals import user_logged_in
from geo.models import IpAsn

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def update_user_ip_info(sender, user, request, **kwargs):
    ip = get_client_ip(request)
    if ip:
        # Check if profile exists
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.ip_address = ip
            
            # Lookup Country
            # PostGIS would allow efficient range queries, but for now we rely on standard Django ORM
            # Assuming start_ip and end_ip are GenericIPAddressField which stores as string in some DBs but 
            # Postgres handles slightly differently. However, standard string comparison or ipaddress module comparison
            # is safer if DB support is mixed. 
            # But since we are using Postgres (based on user context about PostGIS in history), 
            # standard lte/gte on GenericIPAddressField works correctly for IP semantics in Django + Postgres.
            
            try:
                ip_asn = IpAsn.objects.filter(start_ip__lte=ip, end_ip__gte=ip).first()
                if ip_asn:
                    profile.ip_country = ip_asn.country_code
            except Exception as e:
                # Log error or silently fail if IP is invalid or lookup fails
                print(f"Error looking up IP ASN: {e}")
                pass
            
            profile.save()
