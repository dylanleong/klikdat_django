from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ChatRoom, Message

class MessageFilteringTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.client.force_authenticate(user=self.user1)

        self.room1 = ChatRoom.objects.create(name='Room 1', creator=self.user1)
        self.room1.participants.add(self.user1, self.user2)
        
        self.room2 = ChatRoom.objects.create(name='Room 2', creator=self.user1)
        self.room2.participants.add(self.user1, self.user2)

        self.msg1 = Message.objects.create(room=self.room1, sender=self.user1, content="Hello Room 1")
        self.msg2 = Message.objects.create(room=self.room2, sender=self.user1, content="Hello Room 2")

    def test_filter_messages_by_room(self):
        # Filter for Room 1
        response = self.client.get(f'/api/chat/messages/?room_id={self.room1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], "Hello Room 1")

        # Filter for Room 2
        response = self.client.get(f'/api/chat/messages/?room_id={self.room2.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], "Hello Room 2")

    def test_get_all_messages_no_filter(self):
        # No filter
        response = self.client.get('/api/chat/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
