from django.urls import path
from .views import PostsListCreateAPIView

urlpatterns = [
    path('posts/', PostsListCreateAPIView.as_view(), name='posts-list-create'),
    path('posts', PostsListCreateAPIView.as_view()),
]
