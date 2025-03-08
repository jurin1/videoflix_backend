from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from users.serializers import UserSerializer
from users.models import CustomUser, AccountActivationToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from rest_framework import exceptions 


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        activation_token = AccountActivationToken.objects.create(user=user)

        mail_subject = 'Activate your Videoflix account'
        activation_link = self.request.build_absolute_uri(reverse('activate', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)), 'token': activation_token.token}))

        html_message = render_to_string('email.html', {
            'username': user.username,
            'activation_link': activation_link,
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


class LoginView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({'error': 'Ungültige Anmeldeinformationen'}, status=400)


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
        
    