from django.conf import settings
from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    resolutions = models.JSONField(null=True, blank=True)
    genre = models.TextField(blank=True)

    def __str__(self):
        return self.title

class VideoViewing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(auto_now=True)
    watched_duration = models.FloatField(default=0)
    is_finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'video') 

    def __str__(self):
        return f"{self.user.username} viewed {self.video.title} at {self.viewed_at}"