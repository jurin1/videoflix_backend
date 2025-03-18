from django.utils.encoding import force_str
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from users.models import CustomUser, PasswordResetToken
from rest_framework.validators import UniqueValidator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.

    Handles user registration and includes fields for username, email,
    address, phone number, profile picture, and password.
    """
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=CustomUser.objects, message='Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')] # Keeping German message as per original, but should ideally be internationalized or in English if requested to fully translate.
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects, message='Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')] # Keeping German message as per original, same as username.
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        """
        Meta class for UserSerializer.

        Defines the model and fields to be serialized, and extra keyword arguments
        for field customization.
        """
        model = CustomUser
        fields = ('id', 'username', 'email', 'adresse', 'telefon', 'profilbild', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }


    def create(self, validated_data):
        """
        Creates and saves a new CustomUser instance.

        Hashes the password before saving the user.

        Args:
            validated_data (dict): Validated data for user creation.

        Returns:
            CustomUser: The newly created user instance.
        """
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_username(self, value):
        """
        Validates the username.

        Checks if a user with the given username already exists and is active.
        If an inactive user exists, it's deleted to allow reuse of the username.
        If an active user exists, a validation error is raised.

        Args:
            value (str): The username to validate.

        Returns:
            str: The validated username.

        Raises:
            serializers.ValidationError: If an active user with the username exists.
        """
        existing_user = CustomUser.objects.filter(username=value).first()
        if existing_user:
            if not existing_user.is_active:
                existing_user.delete()
                return value
            else:
                raise serializers.ValidationError('Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.') # Keeping German message as per original.
        return value

    def validate_email(self, value):
        """
        Validates the email address.

        Checks if a user with the given email already exists and is active.
        If an inactive user exists, it's deleted to allow reuse of the email.
        If an active user exists, a validation error is raised.

        Args:
            value (str): The email address to validate.

        Returns:
            str: The validated email address.

        Raises:
            serializers.ValidationError: If an active user with the email exists.
        """
        existing_user = CustomUser.objects.filter(email=value).first()
        if existing_user:
            if not existing_user.is_active:
                existing_user.delete()
                return value
            else:
                raise serializers.ValidationError('Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.') # Keeping German message as per original.
        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.

    Takes an email address as input to initiate the password reset process.
    """
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.

    Takes new_password and confirm_password as input to reset the user's password.
    Validates that both passwords match.
    """
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validates that new_password and confirm_password fields match.

        Args:
            data (dict): Input data containing new_password and confirm_password.

        Returns:
            dict: Validated data if passwords match.

        Raises:
            serializers.ValidationError: If passwords do not match.
        """
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwörter stimmen nicht überein.") # Keeping German message as per original.
        return data

    def save(self):
        """
        Saves the new password and invalidates the password reset token.

        Retrieves user and token from serializer context, verifies the token,
        sets the new password, and deletes the used token.

        Raises:
            serializers.ValidationError: If reset link is invalid, token is invalid or expired.
        """
        uidb64 = self.context.get('uidb64')
        token_str = self.context.get('token')
        new_password = self.validated_data.get('new_password')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError('Ungültiger Reset-Link.', code='invalid_link') # Keeping German message as per original.

        try:
            reset_token = PasswordResetToken.objects.get(user=user, token=token_str)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Ungültiger Reset-Link oder Token abgelaufen.', code='invalid_token') # Keeping German message as per original.

        if (reset_token.created_at - timezone.now()).total_seconds() > 3600 :
             raise serializers.ValidationError('Token ist abgelaufen.', code='token_expired') # Keeping German message as per original. # TODO: Token Gültigkeit in Settings - Consider moving this comment to settings or environment variables documentation.

        user.set_password(new_password)
        user.save()
        reset_token.delete()

from django.utils.translation import gettext_lazy as _

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Takes email and password for user authentication. Returns an authentication token upon successful login.
    """
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        """
        Validates user credentials and authenticates the user.

        Authenticates user using email and password. Checks if the user is active.

        Args:
            data (dict): Input data containing email and password.

        Returns:
            dict: Validated data containing the authenticated user.

        Raises:
            serializers.ValidationError: If authentication fails or user is inactive.
        """
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = CustomUser.objects.filter(email=email).first()
            if user:
                user = authenticate(username=user.username, password=password)
                if user:
                    if not user.is_active:
                        raise serializers.ValidationError(_("Benutzerkonto ist deaktiviert.")) # Keeping German message as per original.
                    data['user'] = user
                else:
                    raise serializers.ValidationError(_("Ungültige Anmeldeinformationen.")) # Keeping German message as per original.
            else:
                raise serializers.ValidationError(_("Ungültige Anmeldeinformationen.")) # Keeping German message as per original.
        else:
            raise serializers.ValidationError(_("Email und Passwort sind erforderlich.")) # Keeping German message as per original. # Übersetzbare Fehlermeldung - Comment is redundant as the message is already translatable using _
        return data

from rest_framework import serializers

class AccountActionRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting account actions (like activation or password reset).

    Takes an email address to identify the user for the action.
    """
    email = serializers.EmailField(required=True)