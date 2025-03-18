from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from users.serializers import AccountActionRequestSerializer, PasswordResetRequestSerializer, UserSerializer, LoginSerializer
from users.models import CustomUser, AccountActivationToken
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from rest_framework import exceptions 
from rest_framework import status
from users.serializers import PasswordResetConfirmSerializer
from users.models import PasswordResetToken


User = get_user_model()
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        frontend_url = settings.FRONTEND_URL

        user = serializer.save(is_active=False)
        activation_token = AccountActivationToken.objects.create(user=user)

        mail_subject = 'Activate your Videoflix account'
        activation_link = self.request.build_absolute_uri(reverse('activate', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)), 'token': activation_token.token}))

        html_message = render_to_string('email-activate-account.html', {
            'username': user.username,
            'activation_link': activation_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hello {user.username},

            Please click the link below to activate your Videoflix account:

            {activation_link}

            If you did not register for Videoflix, please ignore this email.

            Thank you,
            The Videoflix Team
        """

        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    def handle_exception(self, exc): 
        if isinstance(exc, exceptions.ValidationError): 
            return Response({'error': 'Konto existiert bereits. Gehe bitte zur Seite Passwort zurücksetzen, falls du dein Passwort vergessen hast.'}, status=400)

        return super().handle_exception(exc)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({'message': 'Erfolgreich ausgeloggt'})


class ActivateAccountView(APIView):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and AccountActivationToken.objects.filter(user=user, token=token).exists():
            user.is_active = True
            user.save()
            AccountActivationToken.objects.filter(user=user).delete()
            return Response({'message': 'Account activated successfully! You can now log in.'})
        else:
            return Response({'error': 'Activation link is invalid!'}, status=400)
        
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        frontend_url = settings.FRONTEND_URL

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Passwort-Reset-Link wurde gesendet, falls ein Konto mit dieser E-Mail-Adresse existiert.'}, status=status.HTTP_200_OK)

        
        PasswordResetToken.objects.filter(user=user).delete() 
        reset_token = PasswordResetToken.objects.create(user=user)

        reset_link = self.build_reset_link(user, reset_token.token, frontend_url)
        self.send_reset_email(user, reset_link, frontend_url)

        return Response({'message': 'Passwort-Reset-Link wurde gesendet, falls ein Konto mit dieser E-Mail-Adresse existiert.'}, status=status.HTTP_200_OK)

    def build_reset_link(self, user, token, frontend_url):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"
         
        
        return reset_link

    def send_reset_email(self, user, reset_link, frontend_url):
        mail_subject = 'Passwort zurücksetzen für Videoflix'
        html_message = render_to_string('email_password_reset.html', { 
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hallo {user.username},

            bitte klicke auf den folgenden Link, um dein Passwort zurückzusetzen:

            {reset_link}

            Wenn du kein Passwort-Reset angefordert hast, ignoriere diese E-Mail einfach.

            Danke,
            Das Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'uidb64': uidb64, 'token': token})
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        return Response({'message': 'Passwort erfolgreich zurückgesetzt.'}, status=status.HTTP_200_OK)
    

class AccountActionRequestView(generics.GenericAPIView):
    serializer_class = AccountActionRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                # Fall 1: Konto aktiv - Passwort vergessen Link senden
                return self.handle_active_user(user, request)
            else:
                # Fall 2: Konto inaktiv - Aktivierungslink senden
                return self.handle_inactive_user(user, request)
        except CustomUser.DoesNotExist:
            # Fall 3: E-Mail nicht gefunden - Registrierungslink zurückgeben
            return self.handle_user_not_found(email, request)

    def handle_active_user(self, user, request):
        """Behandelt den Fall eines aktiven Benutzers."""
        frontend_url = settings.FRONTEND_URL # Stelle sicher, dass FRONTEND_URL in settings.py definiert ist

        # Passwort vergessen Link generieren (kann Logik aus PasswordResetRequestView wiederverwenden oder duplizieren)
        PasswordResetToken.objects.filter(user=user).delete()
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_link = self.build_reset_link(user, reset_token.token, frontend_url) # Funktion build_reset_link wiederverwenden oder duplizieren

        # E-Mail senden (Funktion send_reset_email wiederverwenden oder duplizieren, leicht angepasst)
        self.send_active_account_email(user, reset_link, frontend_url) # Neue Funktion für aktive Konto-E-Mail

        return Response({'message': 'E-Mail gesendet. Überprüfe deinen Posteingang.'}, status=status.HTTP_200_OK) # Generische Erfolgsmeldung

    def handle_inactive_user(self, user, request):
        """Behandelt den Fall eines inaktiven Benutzers."""
        frontend_url = settings.FRONTEND_URL

        # Aktivierungslink generieren (Logik aus RegisterView wiederverwenden oder duplizieren)
        activation_token = AccountActivationToken.objects.create(user=user)
        activation_link = request.build_absolute_uri(reverse('activate', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)), 'token': activation_token.token}))

        # E-Mail senden (Funktion aus RegisterView wiederverwenden oder duplizieren, leicht angepasst)
        self.send_inactive_account_email(user, activation_link, frontend_url) # Neue Funktion für inaktive Konto-E-Mail

        return Response({'message': 'E-Mail gesendet. Überprüfe deinen Posteingang.'}, status=status.HTTP_200_OK) # Generische Erfolgsmeldung

    def handle_user_not_found(self, email, request):
        """Behandelt den Fall, dass die E-Mail nicht gefunden wurde."""
        frontend_url = settings.FRONTEND_URL # Stelle sicher, dass FRONTEND_URL in settings.py definiert ist
        register_url = f"{frontend_url}/register?email={email}" # Frontend-URL für Registrierung mit E-Mail-Parameter
        return Response({'message': 'E-Mail-Adresse nicht gefunden. Du kannst dich hier registrieren.', 'register_url': register_url}, status=status.HTTP_404_NOT_FOUND) # 404 Not Found oder 400 Bad Request möglich

    # Wiederverwende oder dupliziere diese Funktionen aus PasswordResetRequestView (anpassen falls nötig)
    def build_reset_link(self, user, token, frontend_url):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"
        return reset_link

    def send_reset_email(self, user, reset_link, frontend_url): # Wiederverwenden oder leicht anpassen
        mail_subject = 'Passwort zurücksetzen für Videoflix'
        html_message = render_to_string('email_password_reset.html', {
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hallo {user.username},
            bitte klicke auf den folgenden Link, um dein Passwort zurückzusetzen: {reset_link}
            Wenn du kein Passwort-Reset angefordert hast, ignoriere diese E-Mail einfach.
            Danke, Das Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    # Neue E-Mail-Funktionen für aktive und inaktive Konten
    def send_active_account_email(self, user, reset_link, frontend_url):
        mail_subject = 'Videoflix Konto Information' # Angepasster Betreff
        html_message = render_to_string('email_account_info_active.html', { # Neue Template-Datei
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hallo {user.username},
            dein Videoflix-Konto ist bereits aktiv. Wenn du dein Passwort vergessen hast, klicke hier: {reset_link}
            Danke, Das Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    def send_inactive_account_email(self, user, activation_link, frontend_url):
        mail_subject = 'Aktiviere dein Videoflix Konto' # Angepasster Betreff
        html_message = render_to_string('email-activate-account.html', { # Wiederverwende bestehende Template-Datei oder erstelle eine neue leicht angepasste
            'username': user.username,
            'activation_link': activation_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hallo {user.username},
            bitte klicke auf den Link, um dein Videoflix-Konto zu aktivieren: {activation_link}
            Danke, Das Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)