from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from .models import JobPosting, Application, Interview, Resume
from .serializers import (
    JobPostingSerializer, ApplicationSerializer, 
    InterviewSerializer, ResumeSerializer
)
from business.models import BusinessProfile

class JobPostingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Jobs. 
    - List: Publicly available (ReadOnly for candidates).
    - Create/Update: Recruiters only.
    """
    queryset = JobPosting.objects.all().order_by('-created_at')
    serializer_class = JobPostingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'requirements', 'location']

    def get_queryset(self):
        queryset = super().get_queryset()
        # If looking for my jobs (as recruiter)
        user = self.request.user
        if self.action == 'my_jobs' and user.is_authenticated:
             return queryset.filter(recruiter=user)
        
        # Public list should only show Published jobs
        if self.action == 'list':
             queryset = queryset.filter(status=JobPosting.Status.PUBLISHED)
        
        # Filters
        job_type = self.request.query_params.get('job_type')
        if job_type:
             queryset = queryset.filter(job_type=job_type)
        
        workplace_type = self.request.query_params.get('workplace_type')
        if workplace_type:
             queryset = queryset.filter(workplace_type=workplace_type)
        
        salary_min = self.request.query_params.get('salary_min')
        if salary_min:
             queryset = queryset.filter(salary_min__gte=salary_min)
        
        salary_max = self.request.query_params.get('salary_max')
        if salary_max:
             queryset = queryset.filter(salary_max__lte=salary_max)

        return queryset

    def perform_create(self, serializer):
        # Auto-link to the user's business profile
        # Use the first business profile for now
        business = BusinessProfile.objects.filter(owner=self.request.user).first()
        if not business:
            raise serializers.ValidationError("You must have a Business Profile to post jobs.")
        
        serializer.save(recruiter=self.request.user, business=business)

    @action(detail=False, methods=['get'])
    def my_jobs(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Applications.
    - Candidates create applications.
    - Recruiters view applications for their jobs.
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Candidates see their own applications
        # Recruiters see applications for jobs they posted
        return Application.objects.filter(
            models.Q(candidate=user) | 
            models.Q(job_posting__recruiter=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user)

    # Transition Actions
    @action(detail=True, methods=['post'])
    def screen(self, request, pk=None):
        application = self.get_object()
        # Check permission: Only recruiter
        if application.job_posting.recruiter != request.user:
             return Response(status=status.HTTP_403_FORBIDDEN)
        
        # Using FSM transition
        try:
             application.screen()
             application.save()
             return Response({'status': application.status})
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(
            models.Q(application__candidate=user) | 
            models.Q(recruiter=user)
        )

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)
