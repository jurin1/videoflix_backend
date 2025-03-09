from rest_framework import serializers
from .models import Video, VideoViewing

class VideoSerializer(serializers.ModelSerializer):
    genre = serializers.ChoiceField(
        choices=['Action', 'Comedy', 'Documentary', 'Drama'],
        required=True,
        error_messages={
            'required': "Das Genre ist ein Pflichtfeld. Bitte wählen Sie eines der folgenden Genres: Action, Comedy, Documentary, Drama.",
            'invalid_choice': "Ungültiges Genre. Bitte wählen Sie eines der folgenden Genres: Action, Comedy, Documentary, Drama."
        }
    )

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'video_file', 'thumbnail', 'resolutions', 'upload_date', 'genre']
        read_only_fields = ['id', 'thumbnail', 'resolutions', 'upload_date']


class VideoViewingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoViewing
        fields = ['id', 'video', 'viewed_at', 'last_viewed_at', 'watched_duration', 'is_finished']
        read_only_fields = ['id', 'viewed_at', 'last_viewed_at'] 