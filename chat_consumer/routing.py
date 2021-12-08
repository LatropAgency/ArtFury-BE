from django.urls import re_path
from chat_consumer import consumers

websocket_urlpatterns = [
    re_path(r'ws/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
