from django.contrib.auth.models import User
from django.db import models

from core.base_enum import BaseEnum


class DateMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(db_index=True, auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Order(DateMixin):
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=128, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    price = models.BigIntegerField(null=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Image(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    file = models.FileField()


class Comment(DateMixin):
    message = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_comments')


class Chat(DateMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_chats')
    producer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='producer_chats')
    consumer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consumer_chats')


class Message(DateMixin):
    class MessageTypes(BaseEnum):
        TEXT = 1
        IMAGE = 2

    text = models.TextField()
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.PositiveSmallIntegerField(choices=MessageTypes.items())
