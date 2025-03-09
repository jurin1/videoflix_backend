from django.urls import path
from .views import VideoUploadView, StartViewingView, UpdateViewingProgressView, MarkVideoAsFinishedView, GetViewingProgressView, ContinueWatchingListView

urlpatterns = [
    path('upload/', VideoUploadView.as_view(), name='video-upload'),
    path('viewing/start/', StartViewingView.as_view(), name='start-viewing'),
    path('viewing/progress/<int:pk>/', UpdateViewingProgressView.as_view(), name='update-viewing-progress'),
    path('viewing/finished/<int:pk>/', MarkVideoAsFinishedView.as_view(), name='mark-video-finished'),
    path('viewing/get/<int:pk>/', GetViewingProgressView.as_view(), name='get-viewing-progress'),
    path('viewing/continue-watching/', ContinueWatchingListView.as_view(), name='continue-watching-list'),
]