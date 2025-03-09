from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .serializers import VideoSerializer, VideoViewingSerializer
from .models import Video, VideoViewing
from .tasks import convert_video_task


class VideoUploadView(generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        video_instance = serializer.save()
        convert_video_task.delay(video_instance.id)


class StartViewingView(generics.CreateAPIView):
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        video = serializer.validated_data['video']
        user = self.request.user

        viewing, created = VideoViewing.objects.get_or_create(user=user, video=video)
        if not created:
            viewing.save() 
        serializer = VideoViewingSerializer(viewing) 
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UpdateViewingProgressView(generics.UpdateAPIView):
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk' 

    def perform_update(self, serializer):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkVideoAsFinishedView(generics.UpdateAPIView):
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk' 

    def perform_update(self, serializer):
        serializer.save(is_finished=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetViewingProgressView(generics.RetrieveAPIView):
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk' 

class ContinueWatchingListView(generics.ListAPIView):
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return VideoViewing.objects.filter(user=user, is_finished=False, watched_duration__gt=0).order_by('-last_viewed_at')