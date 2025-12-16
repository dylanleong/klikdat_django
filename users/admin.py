from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'dob', 'phone', 'ip_country')
    search_fields = ('user__username', 'user__email', 'phone', 'ip_address')
    list_filter = ('gender', 'ip_country')
