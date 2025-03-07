import os
from celery import Celery

from videoflix_backend.settings import INSTALLED_APPS


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoflix_backend.settings')

app = Celery('videoflix_backend')


app.config_from_object('django.conf:settings', namespace='CELERY')


app.autodiscover_tasks(lambda: INSTALLED_APPS)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')