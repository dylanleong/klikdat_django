from rest_framework import serializers
from .models import JobPosting, Application, Interview, Resume
from django.contrib.auth.models import User
from business.serializers import BusinessProfileSerializer

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'title', 'file', 'uploaded_at', 'is_primary']
        read_only_fields = ['user', 'uploaded_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class JobPostingSerializer(serializers.ModelSerializer):
    business_details = BusinessProfileSerializer(source='business', read_only=True)
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'business', 'business_details', 'recruiter', 'title', 'description', 
            'requirements', 'location', 'salary_min', 'salary_max', 'currency', 
            'job_type', 'workplace_type', 'seniority_level', 'status', 
            'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = ['recruiter', 'created_at', 'updated_at', 'business']

    def create(self, validated_data):
        # Business logic is handled in ViewSet.perform_create
        return super().create(validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    job_details = JobPostingSerializer(source='job_posting', read_only=True)
    resume_details = ResumeSerializer(source='resume', read_only=True)
    candidate_name = serializers.CharField(source='candidate.username', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_posting', 'job_details', 'candidate', 'candidate_name',
            'resume', 'resume_details', 'cover_letter', 'status', 'applied_at', 'updated_at'
        ]
        read_only_fields = ['candidate', 'status', 'applied_at', 'updated_at']

    def create(self, validated_data):
        validated_data['candidate'] = self.context['request'].user
        return super().create(validated_data)

class InterviewSerializer(serializers.ModelSerializer):
    recruiter_name = serializers.CharField(source='recruiter.username', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'recruiter', 'recruiter_name', 'scheduled_at', 
            'duration_minutes', 'interview_type', 'meeting_link', 'notes', 
            'completed_at'
        ]
        read_only_fields = ['recruiter']

    def create(self, validated_data):
        validated_data['recruiter'] = self.context['request'].user
        return super().create(validated_data)
