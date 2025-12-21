from django.contrib import admin
from .models import Profile, VerificationProfile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'dob', 'phone', 'ip_country')
    search_fields = ('user__username', 'user__email', 'phone', 'ip_address')
    list_filter = ('gender', 'ip_country')

@admin.register(VerificationProfile)
class VerificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'v1_email', 'v2_phone', 'v3_location', 'ai_analysis_status', 'level')
    list_filter = ('v1_email', 'v2_phone', 'v3_location', 'ai_analysis_status')
