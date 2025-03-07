from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser 
from .serializers import VideoSerializer
from .models import Video
from .tasks import convert_video_task

class VideoUploadView(generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAdminUser] 
    parser_classes = [MultiPartParser, FormParser] 

    def perform_create(self, serializer):
        video_instance = serializer.save() 
        convert_video_task.delay(video_instance.id)