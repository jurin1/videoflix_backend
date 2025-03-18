from celery import shared_task
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta

@shared_task
def cleanup_inactive_users():
    """
    Deletes inactive users who have not activated their account within 1 day.

    This task is scheduled to run daily and identifies users who registered
    more than 24 hours ago but have not yet activated their accounts
    (is_active=False). These inactive user accounts are then permanently deleted
    from the database to cleanup stale registrations.
    """
    cutoff_date = timezone.now() - timedelta(days=1)
    inactive_users = CustomUser.objects.filter(is_active=False, date_joined__lte=cutoff_date)
    deleted_count = inactive_users.count()
    inactive_users.delete()
    print(f"Celery Task: {deleted_count} inactive users were deleted.")