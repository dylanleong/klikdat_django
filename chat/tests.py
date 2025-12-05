from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ChatRoom

class UserListTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.user3 = User.objects.create_user(username='user3', password='password')
        self.client.force_authenticate(user=self.user1)

    def test_list_users(self):
        response = self.client.get('/api/chat/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return user2 and user3, but not user1
        self.assertEqual(len(response.data['results']), 2)
        usernames = [user['username'] for user in response.data['results']]
        self.assertIn('user2', usernames)
        self.assertIn('user3', usernames)
        self.assertNotIn('user1', usernames)

    def test_list_users_unauthenticated(self):
        self.client.logout()
        response = self.client.get('/api/chat/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ChatRoomCRUDTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.user3 = User.objects.create_user(username='user3', password='password')
        self.client.force_authenticate(user=self.user1)

    def test_create_room(self):
        response = self.client.post('/api/chat/rooms/', {'name': 'Test Room', 'participant_ids': [self.user2.id]})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Room')
        self.assertEqual(response.data['creator']['username'], 'user1')

    def test_update_room_as_creator(self):
        room = ChatRoom.objects.create(name='Old Name', creator=self.user1)
        room.participants.add(self.user1, self.user2)
        response = self.client.patch(f'/api/chat/rooms/{room.id}/', {'name': 'New Name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Name')

    def test_update_room_as_non_creator(self):
        room = ChatRoom.objects.create(name='Old Name', creator=self.user2)
        room.participants.add(self.user1, self.user2)
        response = self.client.patch(f'/api/chat/rooms/{room.id}/', {'name': 'New Name'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_room_as_creator(self):
        room = ChatRoom.objects.create(name='To Delete', creator=self.user1)
        room.participants.add(self.user1, self.user2)
        response = self.client.delete(f'/api/chat/rooms/{room.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatRoom.objects.filter(id=room.id).exists())

    def test_delete_room_as_non_creator(self):
        room = ChatRoom.objects.create(name='To Delete', creator=self.user2)
        room.participants.add(self.user1, self.user2)
        response = self.client.delete(f'/api/chat/rooms/{room.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ChatRoom.objects.filter(id=room.id).exists())

    def test_list_rooms(self):
        # Create a room where user1 is a participant
        room1 = ChatRoom.objects.create(name='Room 1', creator=self.user1)
        room1.participants.add(self.user1, self.user2)
        
        # Create a room where user1 is NOT a participant
        room2 = ChatRoom.objects.create(name='Room 2', creator=self.user2)
        room2.participants.add(self.user2, self.user3)

        response = self.client.get('/api/chat/rooms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see room1
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], room1.id)
