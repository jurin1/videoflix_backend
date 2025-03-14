from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .serializers import VideoSerializer, VideoViewingSerializer
from .models import Video, VideoViewing
from .tasks import convert_video_task
from django.http import StreamingHttpResponse, HttpResponseBadRequest, FileResponse, HttpResponseNotFound
import os
from django.conf import settings
from wsgiref.headers import Headers


class AllVideosListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]


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
        return VideoViewing.objects.filter(user=user, is_finished=False, watched_duration__gt=0).order_by(
            '-last_viewed_at')


def parse_byte_range(range_header):
    """Parsen des HTTP Range Headers."""
    parts = range_header.replace('bytes=', '').split('-')
    start = parts[0]
    end = parts[1]
    if start:
        start = int(start)
    else:
        start = 0
    if end:
        end = int(end)
    else:
        end = None  # Bis zum Ende der Datei
    return start, end


class VideoStreamView(generics.RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    # permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        resolution_name = kwargs.get('resolution')

        if resolution_name:  # Serve specific resolution
            resolutions = instance.resolutions
            if not resolutions or resolution_name not in resolutions:
                return HttpResponseBadRequest(
                    f"Ungültige Auflösung: '{resolution_name}'. Verfügbare Auflösungen: {list(resolutions.keys()) if resolutions else []}")

            # **CORRECTED PATH CONSTRUCTION - USE relative_video_path AS IS**
            relative_video_path = resolutions[resolution_name]
            video_path = os.path.normpath(os.path.join(settings.BASE_DIR, relative_video_path[1:])) # Use normpath to clean up path


        else:  # Serve original video file (no resolution specified in URL)
            # CORRECT PATH CONSTRUCTION for ORIGINAL VIDEO - DIRECT DATABASE PATH
            video_path = instance.video_file.path

        print(f"DEBUG: VideoStreamView - Checking for file existence at path: {video_path}")  # Debug print

        if not os.path.exists(video_path):
            return HttpResponseNotFound(
                f"Video-Datei für Auflösung '{resolution_name}' nicht gefunden: {video_path}")

        file_size = os.path.getsize(video_path)
        start, end = 0, file_size - 1

        chunk_size = 8192

        def video_content_generator(file_path, start_byte, end_byte, chunk_size):
            with open(file_path, 'rb') as video_file:
                video_file.seek(start_byte)
                bytes_to_read = end_byte - start_byte + 1

                while bytes_to_read > 0:
                    chunk = video_file.read(min(chunk_size, bytes_to_read))
                    if not chunk:
                        break
                    yield chunk
                    bytes_to_read -= len(chunk)

        response = StreamingHttpResponse(
            video_content_generator(video_path, start, end, chunk_size),
            status=206,
            content_type='video/mp4'
        )
        response['Content-Length'] = str(end - start + 1)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        return response