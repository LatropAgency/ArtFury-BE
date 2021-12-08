from django.urls import path
from rest_framework.routers import DefaultRouter

from app.views import *

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'comments', CategoryViewSet, basename='comment')
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path('user/', UserAPIView.as_view()),
    path('user/signup/', SignUpAPIView.as_view()),
    path('user/password/', ChangePasswordAPIView.as_view()),
    path('categories/', CategoryAPIView.as_view()),
    path('authors/', AuthorListAPIView.as_view()),
    path('authors/<int:pk>/', AuthorRetrieveAPIView.as_view()),
    path('user/orders/', UserOrderAPIView.as_view()),
] + router.urls
