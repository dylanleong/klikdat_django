from django.contrib import admin
from .models import JobPosting, Application, Interview, Resume

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'recruiter', 'status', 'created_at')
    list_filter = ('status', 'job_type', 'workplace_type')
    search_fields = ('title', 'description')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job_posting', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('candidate__username', 'job_posting__title')

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'recruiter', 'scheduled_at', 'interview_type')
    list_filter = ('interview_type',)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'uploaded_at')
    search_fields = ('user__username', 'title')
