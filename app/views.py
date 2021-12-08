from django.contrib.auth.models import User
from django.http import Http404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from app.filters import OrderPriceFilter
from app.models import Order, Category, Comment, Chat, Message
from app.serializers import (
    ChangePasswordSerializer,
    OrderRetrieveSerializer,
    CommentListSerializer,
    UpdateOrderSerializer,
    MessageListSerializer,
    CreateOrderSerializer,
    CreateChatSerializer,
    OrderListSerializer,
    ChatListSerializer,
    UserListSerializer,
    CategorySerializer,
    CommentSerializer,
    SignUpSerializer,
    UserSerializer,
)


class UserAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class SignUpAPIView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatListSerializer
    permission_classes = (IsAuthenticated,)

    serializer = {
        'list': ChatListSerializer,
        'retrieve': ChatListSerializer,
        'create': CreateChatSerializer,
        'chat_messages': MessageListSerializer
    }

    def get_serializer_class(self):
        return self.serializer.get(self.action, CreateChatSerializer)

    def get_queryset(self):
        return Chat.objects.filter(
            Q(producer=self.request.user) | Q(consumer=self.request.user)
        ).order_by('-created_at')

    @action(methods=('get',), url_path='messages', detail=True)
    def chat_messages(self, request, pk):
        messages = Message.objects.filter(chat_id=pk).order_by('-created_at')
        page = self.paginate_queryset(messages)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ChangePasswordAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class CategoryAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None


class AuthorListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None


class AuthorRetrieveAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)


class UserOrderAPIView(generics.ListAPIView):
    queryset = Order.objects.filter()
    serializer_class = OrderListSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter, OrderPriceFilter]
    search_fields = ['title']
    filter_fields = ['title', 'category']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-created_at']

    serializer = {
        'list': CommentListSerializer,
        'create': CommentSerializer,
    }

    @action(methods=('get',), detail=True)
    def user(self, request, pk):
        try:
            user_comments = self.get_queryset().filter(
                user_id=pk
            ).order_by('-created_at')
        except Http404:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommentListSerializer(user_comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return self.serializer.get(self.action, CreateOrderSerializer)


class OrderViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser,)
    queryset = Order.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateOrderSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, OrderPriceFilter, SearchFilter]
    search_fields = ['title']
    filter_fields = ['title', 'author', 'price', 'category']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']

    serializer = {
        'list': OrderListSerializer,
        'create': CreateOrderSerializer,
        'retrieve': OrderRetrieveSerializer,
        'update': UpdateOrderSerializer
    }

    def create(self, request, *args, **kwargs):
        file_fields = list(request.FILES.keys())
        serializer = self.get_serializer(data=request.data, file_fields=file_fields)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        file_fields = list(request.FILES.keys())
        serializer = self.get_serializer(self.get_object(), data=request.data, file_fields=file_fields, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_object(self):
        order = Order.objects.get(pk=self.kwargs['pk'])
        if not order.is_active and order.author != self.request.user:
            raise Order.DoesNotExist()
        return order

    @action(methods=('get',), url_path='switch', detail=True)
    def switch_order_status(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            order.is_active = not order.is_active
            order.save()
        except Http404:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'is_active': order.is_active}, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return self.serializer.get(self.action, CreateOrderSerializer)
