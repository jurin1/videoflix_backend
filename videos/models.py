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