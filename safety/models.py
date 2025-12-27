from django.db import models
from django.conf import settings
import random
import string

def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class SafetyCircle(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=10, unique=True, default=generate_invite_code)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_circles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SafetyCircleMember(models.Model):
    circle = models.ForeignKey(SafetyCircle, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='circle_memberships')
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('circle', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.circle.name}"
