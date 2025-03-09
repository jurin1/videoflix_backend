from django.utils.encoding import force_str
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from users.models import CustomUser, PasswordResetToken
from django.db.models import Q
from rest_framework.validators import UniqueValidator
from django.utils.http import urlsafe_base64_decode



class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=CustomUser.objects, message='Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects, message='Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')]
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'adresse', 'telefon', 'profilbild', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }


    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_username(self, value):
        existing_user = CustomUser.objects.filter(username=value).first()
        if existing_user:
            if not existing_user.is_active:
                existing_user.delete()
                return value
            else:
                raise serializers.ValidationError('Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')
        return value

    def validate_email(self, value):
        existing_user = CustomUser.objects.filter(email=value).first()
        if existing_user:
            if not existing_user.is_active:
                existing_user.delete()
                return value
            else:
                raise serializers.ValidationError('Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.')
        return value
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwörter stimmen nicht überein.")
        return data

    def save(self):
        uidb64 = self.context.get('uidb64')
        token_str = self.context.get('token')
        new_password = self.validated_data.get('new_password')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError('Ungültiger Reset-Link.', code='invalid_link')

        try:
            reset_token = PasswordResetToken.objects.get(user=user, token=token_str)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Ungültiger Reset-Link oder Token abgelaufen.', code='invalid_token')

        if (reset_token.created_at - timezone.now()).total_seconds() > 3600 : 
             raise serializers.ValidationError('Token ist abgelaufen.', code='token_expired') # TODO: Token Gültigkeit in Settings

        user.set_password(new_password)
        user.save()
        reset_token.delete() 
