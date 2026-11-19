from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    MeAPIView,
    UserListCreateAPIView,
    UserDetailAPIView,
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterAPIView.as_view(), name='auth-register'),
    path('auth/register', RegisterAPIView.as_view()),
    path('auth/login/', LoginAPIView.as_view(), name='auth-login'),
    path('auth/login', LoginAPIView.as_view()),
    path('auth/me/', MeAPIView.as_view(), name='auth-me'),
    path('auth/me', MeAPIView.as_view()),

    # User management endpoints
    path('users/', UserListCreateAPIView.as_view(), name='users-list-create'),
    path('users', UserListCreateAPIView.as_view()),
    path('users/<str:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('users/<str:pk>', UserDetailAPIView.as_view()),
]
