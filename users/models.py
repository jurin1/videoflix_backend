from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.conf import settings

class CustomUser(AbstractUser):
    adresse = models.CharField(max_length=255, blank=True)
    telefon = models.CharField(max_length=20, blank=True)
    profilbild = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.username
    
class AccountActivationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Activation Token for {self.user.username}"