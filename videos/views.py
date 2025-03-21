from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .serializers import VideoSerializer, VideoViewingSerializer
from .models import Video, VideoViewing
from .tasks import convert_video_task
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseBadRequest, HttpResponseNotFound
import os
from django.conf import settings
from wsgiref.headers import Headers


class AllVideosListView(generics.ListAPIView):
    """
    API view to list all videos.

    Accessible to authenticated users, this view retrieves and lists all available
    videos from the database, using VideoSerializer for serialization.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]


class VideoUploadView(generics.CreateAPIView):
    """
    API view for uploading new videos.

    Accessible only to admin users, this view allows for uploading new video files.
    It uses MultiPartParser and FormParser to handle file uploads and triggers
    a background task (convert_video_task) to process the uploaded video.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        """
        Performs video creation and triggers video conversion task.

        Overrides the default perform_create to initiate the video conversion
        task after successfully saving the video instance.
        """
        video_instance = serializer.save()
        convert_video_task.delay(video_instance.id)


class StartViewingView(generics.CreateAPIView):
    """
    API view to start viewing a video.

    Accessible to authenticated users, this view handles the start of video viewing.
    It creates or retrieves a VideoViewing instance for the user and video,
    marking the beginning of a viewing session.
    """
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Creates or retrieves a VideoViewing instance upon starting to view a video.

        If a VideoViewing instance already exists for the user and video, it retrieves
        the existing instance; otherwise, it creates a new one.
        """
        video = serializer.validated_data['video']
        user = self.request.user

        viewing, created = VideoViewing.objects.get_or_create(user=user, video=video)
        if not created:
            viewing.save()
        serializer = VideoViewingSerializer(viewing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UpdateViewingProgressView(generics.UpdateAPIView):
    """
    API view to update video viewing progress.

    Accessible to authenticated users, this view allows for updating the viewing
    progress of a video, such as watched duration.
    """
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        """
        Updates the VideoViewing instance with provided data.

        Saves the updated VideoViewing instance, typically used to record
        the current watched duration of a video.
        """
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkVideoAsFinishedView(generics.UpdateAPIView):
    """
    API view to mark a video as finished.

    Accessible to authenticated users, this view is used to mark a video as
    completely watched by setting the is_finished field in the VideoViewing model.
    """
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        """
        Updates the VideoViewing instance to mark the video as finished.

        Sets the is_finished attribute of the VideoViewing instance to True,
        indicating that the user has completed watching the video.
        """
        serializer.save(is_finished=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetViewingProgressView(generics.RetrieveAPIView):
    """
    API view to retrieve video viewing progress.

    Accessible to authenticated users, this view retrieves and returns the
    viewing progress of a specific video for the authenticated user.
    """
    queryset = VideoViewing.objects.all()
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'


class ContinueWatchingListView(generics.ListAPIView):
    """
    API view to list videos for 'continue watching'.

    Accessible to authenticated users, this view lists videos that the user
    has started watching but not finished, ordered by the last viewed time.
    """
    serializer_class = VideoViewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the queryset of videos to continue watching.

        Filters VideoViewing instances to include only those that are not finished,
        have a watched duration greater than zero, and orders them by the last viewed time.
        """
        user = self.request.user
        return VideoViewing.objects.filter(user=user, is_finished=False, watched_duration__gt=0).order_by(
            '-last_viewed_at')


def parse_byte_range(range_header):
    """
    Parses the HTTP Range header.

    Extracts the start and end byte ranges from the HTTP Range header,
    handling cases where start or end values are omitted.

    Args:
        range_header (str): The HTTP Range header string.

    Returns:
        tuple: A tuple containing the start and end byte range as integers.
               End range might be None if not specified in the header.
    """
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
        end = None  # Until the end of the file
    return start, end


class VideoStreamView(generics.RetrieveAPIView):
    """
    API view to stream video content.

    This view streams video content, supporting range requests for seeking and
    adaptive streaming. It can serve video in different resolutions if available,
    or the original uploaded video file.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    # permission_classes = [permissions.IsAuthenticated] 
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        """
        Handles video streaming requests.

        Retrieves the video instance and determines the video path based on
        the requested resolution (if any). It then prepares and returns a
        StreamingHttpResponse to stream the video content, supporting byte range
        requests for efficient seeking and playback.
        """
        instance = self.get_object()
        resolution_name = kwargs.get('resolution')

        if resolution_name:  
            resolutions = instance.resolutions
            if not resolutions or resolution_name not in resolutions:
                return HttpResponseBadRequest(
                    f"Invalid resolution: '{resolution_name}'. Available resolutions: {list(resolutions.keys()) if resolutions else []}")

            relative_video_path = resolutions[resolution_name]
            video_path = os.path.normpath(os.path.join(settings.BASE_DIR, relative_video_path[1:])) # Use normpath to clean up path


        else:  
            video_path = instance.video_file.path

        print(f"DEBUG: VideoStreamView - Checking for file existence at path: {video_path}")  # Debug print - Consider removing or using a proper logging setup

        if not os.path.exists(video_path):
            return HttpResponseNotFound(
                f"Video file for resolution '{resolution_name}' not found: {video_path}")

        file_size = os.path.getsize(video_path)
        start, end = 0, file_size - 1

        chunk_size = 8192

        def video_content_generator(file_path, start_byte, end_byte, chunk_size):
            """
            Generator function to yield video content in chunks.

            Reads and yields chunks of video content from the file, starting from
            start_byte up to end_byte, in specified chunk sizes.
            """
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
    
class ThumbnailStreamView(generics.RetrieveAPIView):
    """
    API view to stream thumbnail images.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    # permission_classes = [permissions.IsAuthenticated] # Optional: Aktivieren Sie dies, wenn Thumbnails geschützt sein sollen
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        thumbnail_path_relative = instance.thumbnail.path 
        thumbnail_path_absolute = os.path.join(settings.MEDIA_ROOT, thumbnail_path_relative)
        print(f"DEBUG: ThumbnailStreamView - Checking for thumbnail at path: {thumbnail_path_absolute}") 

        if not os.path.exists(thumbnail_path_absolute):
            return HttpResponseNotFound(f"Thumbnail not found at: {thumbnail_path_absolute}")

        try:
            with open(thumbnail_path_absolute, 'rb') as f:
                return HttpResponse(f.read(), content_type="image/jpeg") 
        except IOError:
            return HttpResponseNotFound("Could not read thumbnail file")