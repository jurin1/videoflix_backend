from django.conf import settings
from django.db import models

class Video(models.Model):
    """
    Model representing a video.

    Stores video details such as title, description, upload date, video file,
    thumbnail, available resolutions, and genre.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    resolutions = models.JSONField(null=True, blank=True)
    genre = models.TextField(blank=True)

    def __str__(self):
        """
        Returns the title of the video as its string representation.
        """
        return self.title

class VideoViewing(models.Model):
    """
    Model to track video viewing history for users.

    Records when a user views a video, the duration watched, and whether
    the video was finished. Ensures that each user's viewing history for a
    specific video is unique.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(auto_now=True)
    watched_duration = models.FloatField(default=0)
    is_finished = models.BooleanField(default=False)

    class Meta:
        """
        Meta class for VideoViewing model.

        Defines constraints and configurations for the model, including
        setting up a unique constraint for user and video combination.
        """
        unique_together = ('user', 'video')

    def __str__(self):
        """
        Returns a string representation of the VideoViewing instance.

        Includes the username of the user, the title of the video, and the
        date and time when it was first viewed.
        """
        return f"{self.user.username} viewed {self.video.title} at {self.viewed_at}"