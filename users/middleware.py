from django.contrib.gis.geoip2 import GeoIP2
from .models import VerificationProfile

class GeoIPVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # We only do this check for specific paths or if not already verified?
            # To avoid overhead on every request, we could check if profile.v3_location is False
            try:
                profile = VerificationProfile.objects.get(user=request.user)
                if not profile.v3_location:
                    ip = self.get_client_ip(request)
                    if ip and ip != '127.0.0.1':
                        g = GeoIP2()
                        country = g.country(ip)
                        # We store the detected country in request metadata for the view to use
                        request.META['GEOIP_COUNTRY'] = country.get('country_code')
            except Exception:
                pass

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
