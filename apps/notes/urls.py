from django.urls import path
from .views import MyNotesAPIView, AllNotesAdminAPIView, NoteDetailAPIView

urlpatterns = [
    path('notes/', MyNotesAPIView.as_view(), name='notes-list-create'),
    path('notes', MyNotesAPIView.as_view()),
    path('notes/all/', AllNotesAdminAPIView.as_view(), name='notes-admin-all'),
    path('notes/all', AllNotesAdminAPIView.as_view()),
    path('notes/<str:pk>/', NoteDetailAPIView.as_view(), name='note-detail'),
    path('notes/<str:pk>', NoteDetailAPIView.as_view()),
]
