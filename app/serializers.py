from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile

from app.models import Order, Category, Comment, Chat, Message, Image


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')


class CreateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('id', 'order', 'producer', 'consumer', 'created_at')
        read_only_fields = ('id', 'created_at')


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'password', 'password2')
        read_only_fields = ('id',)
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class OrderListSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    category = CategorySerializer()

    class Meta:
        model = Order
        fields = ('id', 'title', 'description', 'author', 'is_active', 'price', 'category', 'created_at')


class ImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'file')


class OrderRetrieveSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    category = CategorySerializer()
    chat = serializers.SerializerMethodField()
    image_set = serializers.ListSerializer(child=ImageListSerializer(), read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'title',
            'image_set',
            'description',
            'author',
            'is_active',
            'price',
            'category',
            'created_at',
            'chat',
        )

    def get_chat(self, order: Order):
        chat = order.order_chats.filter(
            Q(producer=self.context['request'].user) | Q(consumer=self.context['request'].user)).first()
        return chat.id if chat else None


class UpdateOrderSerializer(serializers.ModelSerializer):
    images = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        validated_data_copy = validated_data.copy()
        validated_files = []
        for key, value in validated_data_copy.items():
            if isinstance(value, TemporaryUploadedFile) or isinstance(value, InMemoryUploadedFile):
                validated_files.append(value)
                validated_data.pop(key)
        order_instance = super(UpdateOrderSerializer, self).update(instance, validated_data)
        image_ids = [int(str_id) for str_id in validated_data['images'].split(',') if str_id]
        Image.objects.filter(order=instance).exclude(id__in=image_ids).delete()
        for file in validated_files:
            Image.objects.create(order=order_instance, file=file)
        return order_instance

    def __init__(self, *args, **kwargs):
        file_fields = kwargs.pop('file_fields', None)
        super().__init__(*args, **kwargs)
        if file_fields:
            field_update_dict = {field: serializers.FileField(required=False, write_only=True) for field in file_fields}
            self.fields.update(**field_update_dict)

    class Meta:
        model = Order
        fields = ('id', 'title', 'description', 'author', 'is_active', 'price', 'category', 'created_at', 'images')
        read_only_fields = ('id', 'author', 'is_active', 'created_at')

class CreateOrderSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data_copy = validated_data.copy()
        validated_files = []
        for key, value in validated_data_copy.items():
            if isinstance(value, TemporaryUploadedFile) or isinstance(value, InMemoryUploadedFile):
                validated_files.append(value)
                validated_data.pop(key)
        order_instance = super(CreateOrderSerializer, self).create(validated_data)
        for file in validated_files:
            Image.objects.create(order=order_instance, file=file)
        return order_instance

    def __init__(self, *args, **kwargs):
        file_fields = kwargs.pop('file_fields', None)
        super().__init__(*args, **kwargs)
        if file_fields:
            field_update_dict = {field: serializers.FileField(required=False, write_only=True) for field in file_fields}
            self.fields.update(**field_update_dict)

    class Meta:
        model = Order
        fields = ('id', 'title', 'description', 'author', 'is_active', 'price', 'category', 'created_at')
        read_only_fields = ('id', 'author', 'is_active', 'created_at')


class CommentListSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    user = UserListSerializer()

    class Meta:
        model = Comment
        fields = ('id', 'user', 'author', 'message', 'created_at')


class ShortUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class ShortOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'title')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'author', 'message')
        read_only_fields = ('id', 'author')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super(CommentSerializer, self).create(validated_data)


class ChatListSerializer(serializers.ModelSerializer):
    order = ShortOrderSerializer()
    producer = UserListSerializer()
    consumer = UserListSerializer()

    class Meta:
        model = Chat
        fields = ('id', 'order', 'producer', 'consumer', 'created_at')
        read_only_fields = ('id', 'created_at')


class MessageListSerializer(serializers.ModelSerializer):
    sender = ShortUserSerializer()

    class Meta:
        model = Message
        fields = ('id', 'text', 'sender', 'message_type', 'created_at')
