from django.urls import path
from .views import UsersByInterestAggregationView, UserPostsAggregationView

urlpatterns = [
    path('aggregations/users-by-interest/', UsersByInterestAggregationView.as_view(), name='users-by-interest'),
    path('aggregations/users-by-interest', UsersByInterestAggregationView.as_view()),
    path('aggregations/user-posts/<str:userId>/', UserPostsAggregationView.as_view(), name='user-posts-lookup'),
    path('aggregations/user-posts/<str:userId>', UserPostsAggregationView.as_view()),
]
