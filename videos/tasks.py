from celery import shared_task
import subprocess
import os
import uuid 
from django.conf import settings 
from .models import Video
from .utils import sanitize_filename

@shared_task
def convert_video_task(video_id):
    video = Video.objects.get(pk=video_id)
    video_path = video.video_file.path
    
    original_filename_without_extension = os.path.splitext(os.path.basename(video.video_file.name))[0] 
    sanitized_filename = sanitize_filename(original_filename_without_extension) 
    video_folder_name = f"{video.id}_{sanitized_filename}" 
    output_base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', video_folder_name) 
    os.makedirs(output_base_dir, exist_ok=True) 
    resolutions = {
        "120p": "120p.mp4",
        "360p": "360p.mp4",
        "720p": "720p.mp4",
        "1080p": "1080p.mp4",
    }
    converted_resolutions_urls = {} 
    for resolution_name, output_filename in resolutions.items():
        output_path = os.path.join(output_base_dir, output_filename) 
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'scale=trunc(oh*a/2)*2:{resolution_name[:-1]}',
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '22',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg Konvertierung fehlgeschlagen für Auflösung {resolution_name}:")
            print(f"Befehl: {' '.join(command)}")
            print(f"Return Code: {e.returncode}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            raise e
        
        
        relative_url = os.path.join(settings.MEDIA_URL, 'videos', video_folder_name, output_filename).replace('\\', '/') 
        converted_resolutions_urls[resolution_name] = relative_url 
    thumbnail_filename = 'thumbnail.jpg' 
    thumbnail_path = os.path.join(output_base_dir, thumbnail_filename) 
    thumbnail_command = [
        'ffmpeg',
        '-i', video_path,
        '-ss', '00:00:30',
        '-vframes', '1',
        '-vf', 'scale=320:-1',
        thumbnail_path
    ]
    subprocess.run(thumbnail_command, capture_output=True, text=True, check=True)
    thumbnail_relative_url = os.path.join('videos', video_folder_name, thumbnail_filename).replace('\\', '/')    
    video.resolutions = converted_resolutions_urls 
    video.thumbnail = thumbnail_relative_url 
    video.save()