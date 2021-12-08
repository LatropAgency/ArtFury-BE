import datetime
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from app.models import Message
from app.serializers import MessageListSerializer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """
        Connect to a chat room
        Spaces are replaced like this: 'My new room' -> 'My_new_room'
        """

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_id = 'chat_%s' % self.chat_id

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.chat_group_id,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chat_group_id,
            self.channel_name
        )

    def receive(self, text_data):
        """
        Receive a message and broadcast it to a room group
        UTC time is included so the client can display it in each user's local time
        """

        text_data_json = json.loads(text_data)
        text = text_data_json['text']
        chat_id = text_data_json['chat_id']
        sender_id = text_data_json['sender_id']
        message_type = text_data_json['message_type']

        async_to_sync(self.channel_layer.group_send)(
            self.chat_group_id,
            {
                'type': 'chat_message',
                'text': text,
                'chat_id': chat_id,
                'sender_id': sender_id,
                'message_type': message_type,
            }
        )

    def chat_message(self, event):
        """
        Receive a broadcast message and send it over a websocket
        """

        text = event['text']
        chat_id = event['chat_id']
        sender_id = event['sender_id']
        message_type = event['message_type']
        message = Message.objects.create(
            text=text,
            chat_id=chat_id,
            sender_id=sender_id,
            message_type=message_type
        )
        serializer = MessageListSerializer(message)
        # Send message to WebSocket
        self.send(text_data=json.dumps(serializer.data))
