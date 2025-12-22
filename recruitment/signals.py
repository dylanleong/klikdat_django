from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Application, Interview

@receiver(post_save, sender=Application)
def notify_application_update(sender, instance, created, **kwargs):
    if created:
        # Notify Candidate
        send_mail(
            subject=f"Application Received: {instance.job_posting.title}",
            message=f"Hi {instance.candidate.username},\n\nWe have received your application for {instance.job_posting.title}. We will review it shortly.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.candidate.email],
            fail_silently=True
        )
        # Notify Recruiter
        if instance.job_posting.recruiter and instance.job_posting.recruiter.email:
             send_mail(
                subject=f"New Application: {instance.job_posting.title}",
                message=f"New candidate {instance.candidate.username} applied.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.job_posting.recruiter.email],
                fail_silently=True
            )
    else:
        # Notify Status Change
        send_mail(
            subject=f"Application Update: {instance.job_posting.title}",
            message=f"Hi {instance.candidate.username},\n\nYour application status has changed to: {instance.status}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.candidate.email],
            fail_silently=True
        )

@receiver(post_save, sender=Interview)
def notify_interview_scheduled(sender, instance, created, **kwargs):
    if created:
        app = instance.application
        send_mail(
            subject="Interview Scheduled",
            message=f"Hi {app.candidate.username},\n\nAn interview has been scheduled for {instance.scheduled_at}. Type: {instance.interview_type}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[app.candidate.email],
            fail_silently=True
        )
