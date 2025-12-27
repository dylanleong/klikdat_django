import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        print(f"WebSocket Received: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            sender_id = text_data_json.get('sender_id') # Or get from scope if authenticated
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            return
        except KeyError as e:
            print(f"Key Error: {e}")
            return

        # Save message to database
        try:
            username = await self.save_message(self.room_id, sender_id, message)
        except Exception as e:
            print(f"Error saving message: {e}")
            return

        print(f"Broadcasting message from {username}: {message}")
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'username': username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        print(f"Group Received: {event}")
        message = event['message']
        sender_id = event['sender_id']
        username = event.get('username', 'Unknown')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'username': username
        }))

    @database_sync_to_async
    def save_message(self, room_id, sender_id, message):
        try:
            from users.models import Notification
            room = ChatRoom.objects.get(id=room_id)
            sender = User.objects.get(id=sender_id)
            Message.objects.create(room=room, sender=sender, content=message)
            
            # Notify others
            for participant in room.participants.all():
                if participant.id != sender.id:
                    Notification.objects.create(
                        user=participant,
                        type='message',
                        title=f'New message from {sender.username}',
                        body=message[:50] + ('...' if len(message) > 50 else ''),
                        data={'chat_room_id': room.id}
                    )
            return sender.username
        except Exception as e:
            print(f"Database Error in save_message: {e}")
            raise e
