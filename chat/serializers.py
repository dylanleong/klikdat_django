from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='sender', write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'sender_id', 'content', 'timestamp']

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='participants', write_only=True, many=True)

    creator = UserSerializer(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'creator', 'participants', 'participant_ids', 'created_at']
