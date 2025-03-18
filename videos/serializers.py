from rest_framework import serializers
from .models import Video, VideoViewing

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.

    Handles serialization and deserialization of Video instances.
    Includes a ChoiceField for the 'genre' field with predefined choices
    and custom error messages.
    """
    genre = serializers.ChoiceField(
        choices=['Action', 'Comedy', 'Documentary', 'Drama'],
        required=True,
        error_messages={
            'required': "Das Genre ist ein Pflichtfeld. Bitte wählen Sie eines der folgenden Genres: Action, Comedy, Documentary, Drama.", # Keeping German message as per original, should be translated or internationalized in a real application.
            'invalid_choice': "Ungültiges Genre. Bitte wählen Sie eines der folgenden Genres: Action, Comedy, Documentary, Drama." # Keeping German message as per original, same as above.
        }
    )

    class Meta:
        """
        Meta class for VideoSerializer.

        Defines the model to be serialized and the fields to include,
        as well as specifying read-only fields.
        """
        model = Video
        fields = ['id', 'title', 'description', 'video_file', 'thumbnail', 'resolutions', 'upload_date', 'genre']
        read_only_fields = ['id', 'thumbnail', 'resolutions', 'upload_date']


class VideoViewingSerializer(serializers.ModelSerializer):
    """
    Serializer for the VideoViewing model.

    Handles serialization and deserialization of VideoViewing instances.
    Specifies read-only fields for this serializer.
    """
    class Meta:
        """
        Meta class for VideoViewingSerializer.

        Defines the model to be serialized and the fields to include,
        as well as specifying read-only fields.
        """
        model = VideoViewing
        fields = ['id', 'video', 'viewed_at', 'last_viewed_at', 'watched_duration', 'is_finished']
        read_only_fields = ['id', 'viewed_at', 'last_viewed_at']