from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', null=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    
    MODULE_CHOICES = [
        ('matchmake', 'Matchmake'),
        ('vehicle', 'Vehicle'),
        ('recruitment', 'Recruitment'),
        ('property', 'Property'),
    ]
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.id})"
        return f"ChatRoom {self.id} - {', '.join([user.username for user in self.participants.all()])}"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
