from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.conf import settings

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model adds additional fields to the default Django user model
    to store extra user information like address, phone number, and profile picture.
    """
    adresse = models.CharField(max_length=255, blank=True)
    telefon = models.CharField(max_length=20, blank=True)
    profilbild = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        """
        Returns the username of the CustomUser instance.
        """
        return self.username

class AccountActivationToken(models.Model):
    """
    Model to store account activation tokens for users.

    Each token is associated with a user and is used to verify the user's
    email address during account activation. The token is a unique UUID.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the AccountActivationToken.

        This string includes the username of the associated user.
        """
        return f"Activation Token for {self.user.username}"

class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens for users.

    Each token is associated with a user and is used to verify the user's
    request to reset their password. The token is a unique UUID.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the PasswordResetToken.

        This string includes the username of the associated user.
        """
        return f"Password Reset Token for {self.user.username}"