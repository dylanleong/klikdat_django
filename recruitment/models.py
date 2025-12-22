from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from business.models import BusinessProfile

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=100, help_text="e.g. 'Software Engineer CV'")
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            Resume.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class JobPosting(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'FT', _('Full Time')
        PART_TIME = 'PT', _('Part Time')
        CONTRACT = 'CT', _('Contract')
        INTERNSHIP = 'IN', _('Internship')

    class WorkplaceType(models.TextChoices):
        ONSITE = 'ON', _('On-site')
        REMOTE = 'RE', _('Remote')
        HYBRID = 'HY', _('Hybrid')
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PUBLISHED = 'PUBLISHED', _('Published')
        CLOSED = 'CLOSED', _('Closed')

    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='job_postings')
    recruiter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posted_jobs')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    
    location = models.CharField(max_length=200)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    job_type = models.CharField(max_length=2, choices=JobType.choices, default=JobType.FULL_TIME)
    workplace_type = models.CharField(max_length=2, choices=WorkplaceType.choices, default=WorkplaceType.ONSITE)
    seniority_level = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.business.name}"

class Application(models.Model):
    class Stage(models.TextChoices):
        APPLIED = 'APPLIED', _('Applied')
        SCREENING = 'SCREENING', _('Screening')
        INTERVIEW = 'INTERVIEW', _('Interview')
        OFFER = 'OFFER', _('Offer')
        REJECTED = 'REJECTED', _('Rejected')
        WITHDRAWN = 'WITHDRAWN', _('Withdrawn')

    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True)
    cover_letter = models.TextField(blank=True)
    
    status = FSMField(default=Stage.APPLIED, choices=Stage.choices)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job_posting', 'candidate']

    def __str__(self):
        return f"{self.candidate.username} for {self.job_posting.title}"

    # State Transitions
    @transition(field=status, source=Stage.APPLIED, target=Stage.SCREENING)
    def screen(self):
        pass

    @transition(field=status, source=[Stage.APPLIED, Stage.SCREENING], target=Stage.INTERVIEW)
    def schedule_interview(self):
        pass

    @transition(field=status, source=Stage.INTERVIEW, target=Stage.OFFER)
    def make_offer(self):
        pass

    @transition(field=status, source=[Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW, Stage.OFFER], target=Stage.REJECTED)
    def reject(self):
        pass

    @transition(field=status, source='*', target=Stage.WITHDRAWN)
    def withdraw(self):
        pass

class Interview(models.Model):
    class InterviewType(models.TextChoices):
        PHONE = 'PHONE', _('Phone Screen')
        VIDEO = 'VIDEO', _('Video Call')
        ONSITE = 'ONSITE', _('On-site Interview')

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_interviews')
    
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    interview_type = models.CharField(max_length=10, choices=InterviewType.choices, default=InterviewType.VIDEO)
    meeting_link = models.URLField(blank=True)
    
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Interview for {self.application} with {self.recruiter.username}"
