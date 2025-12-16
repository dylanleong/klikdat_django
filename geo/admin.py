from django.contrib import admin
from .models import IpAsn

@admin.register(IpAsn)
class IpAsnAdmin(admin.ModelAdmin):
    list_display = ('start_ip', 'end_ip', 'asn', 'country_code', 'organization')
    search_fields = ('start_ip', 'end_ip', 'organization')
