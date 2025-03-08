from celery import shared_task
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta

@shared_task
def cleanup_inactive_users():
    """Löscht täglich inaktive Benutzer, die älter als 1 Tag sind."""
    cutoff_date = timezone.now() - timedelta(days=1)
    inactive_users = CustomUser.objects.filter(is_active=False, date_joined__lte=cutoff_date)
    deleted_count = inactive_users.count() # Optional: Zähle gelöschte Benutzer
    inactive_users.delete()
    print(f"Celery Task: {deleted_count} inaktive Benutzer wurden gelöscht.") # Optional: Log-Ausgabe