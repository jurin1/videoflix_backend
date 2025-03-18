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
    """
    API view for user registration.

    Allows any user to register a new account. Upon successful registration,
    an account activation email is sent to the user's provided email address.
    The account is initially inactive until the user activates it via the link
    in the email.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """
        Performs the creation of a new user and sends an activation email.

        Overrides the default `perform_create` to set the user as inactive
        upon creation and to send an activation email to the user.

        Args:
            serializer: The serializer instance containing the validated data.
        """
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
        """
        Handles exceptions during user registration.

        Overrides the default `handle_exception` to provide a custom error
        response when a validation error occurs, specifically for duplicate
        account registration attempts.

        Args:
            exc: The exception instance.

        Returns:
            Response: A custom error response if the exception is a ValidationError
                      related to account existence, otherwise the default exception response.
        """
        if isinstance(exc, exceptions.ValidationError):
            return Response({'error': 'Account already exists. Please go to the password reset page if you have forgotten your password.'}, status=400)

        return super().handle_exception(exc)

class LoginView(generics.GenericAPIView):
    """
    API view for user login.

    Authenticates users based on email and password. Upon successful
    authentication, an authentication token is generated and returned to the user.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handles user login requests.

        Validates user credentials using LoginSerializer and, upon successful
        validation, generates or retrieves an authentication token for the user.

        Args:
            request: The HTTP request object containing user login details.

        Returns:
            Response: A response containing the authentication token if login is
                      successful, or an error response if login fails.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LogoutView(generics.GenericAPIView):
    """
    API view for user logout.

    Invalidates the user's authentication token, effectively logging them out.
    Requires user to be authenticated to perform logout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Handles user logout requests.

        Deletes the authentication token associated with the current user,
        thereby logging the user out.

        Args:
            request: The HTTP request object.

        Returns:
            Response: A success message indicating successful logout.
        """
        request.auth.delete()
        return Response({'message': 'Successfully logged out'})


class ActivateAccountView(APIView):
    """
    API view for account activation.

    Activates a user account based on the provided user ID (uidb64) and token.
    Verifies the token against the stored activation tokens and activates the
    user account if valid.
    """
    def get(self, request, uidb64, token, *args, **kwargs):
        """
        Handles account activation requests.

        Verifies the user ID and activation token provided in the URL. If valid,
        activates the corresponding user account and deletes the activation token.

        Args:
            request: The HTTP request object.
            uidb64: The base64 encoded user ID.
            token: The activation token.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A success message upon successful activation, or an error
                      message if the activation link is invalid.
        """
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
    """
    API view to request a password reset.

    Takes an email address, and if a user with that email exists, sends
    a password reset link to the email address.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles password reset requests.

        Validates the email provided in the request and, if a user with that
        email exists, generates a password reset token and sends a reset link
        to the user's email address.

        Args:
            request: The HTTP request object containing the email.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A success message indicating that a password reset link
                      has been sent (or would be sent if the email exists).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        frontend_url = settings.FRONTEND_URL

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Password reset link was sent if an account with this email address exists.'}, status=status.HTTP_200_OK)


        PasswordResetToken.objects.filter(user=user).delete()
        reset_token = PasswordResetToken.objects.create(user=user)

        reset_link = self.build_reset_link(user, reset_token.token, frontend_url)
        self.send_reset_email(user, reset_link, frontend_url)

        return Response({'message': 'Password reset link was sent if an account with this email address exists.'}, status=status.HTTP_200_OK)

    def build_reset_link(self, user, token, frontend_url):
        """
        Builds the password reset link.

        Constructs the full password reset URL using the frontend URL,
        user ID (encoded), and reset token.

        Args:
            user: The CustomUser instance.
            token: The password reset token.
            frontend_url: The frontend application URL.

        Returns:
            str: The complete password reset URL.
        """
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"


        return reset_link

    def send_reset_email(self, user, reset_link, frontend_url):
        """
        Sends the password reset email to the user.

        Renders the password reset email template and sends the email
        to the user's registered email address.

        Args:
            user: The CustomUser instance.
            reset_link: The password reset URL.
            frontend_url: The frontend application URL.
        """
        mail_subject = 'Reset your Videoflix password'
        html_message = render_to_string('email_password_reset.html', {
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hello {user.username},

            Please click on the following link to reset your password:

            {reset_link}

            If you did not request a password reset, please ignore this email.

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


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view to confirm and complete the password reset process.

    Takes a new password and confirmation token to reset the user's password.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        """
        Handles password reset confirmation requests.

        Validates the new password and token provided in the request. If valid,
        resets the user's password and invalidates the reset token.

        Args:
            request: The HTTP request object containing the new password and token.
            uidb64: The base64 encoded user ID.
            token: The password reset token.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A success message upon successful password reset, or an
                      error message if the reset process fails.
        """
        serializer = self.get_serializer(data=request.data, context={'uidb64': uidb64, 'token': token})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)


class AccountActionRequestView(generics.GenericAPIView):
    """
    API view to handle generic account action requests based on email.

    This view determines if an account exists for the given email and whether
    it's active or inactive. Based on the account status, it triggers either
    a password reset flow for active accounts or an account activation flow
    for inactive accounts. If no account is found, it provides a registration link.
    """
    serializer_class = AccountActionRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles account action requests based on email.

        Determines the appropriate action (password reset, account activation,
        or registration link) based on the user's account status and sends
        the corresponding email or response.

        Args:
            request: The HTTP request object containing the email.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A response indicating the action taken, which could be
                      sending an email for password reset or account activation,
                      or providing a registration link if the email is not found.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                # Case 1: Account active - send password reset link
                return self.handle_active_user(user, request)
            else:
                # Case 2: Account inactive - send activation link
                return self.handle_inactive_user(user, request)
        except CustomUser.DoesNotExist:
            # Case 3: Email not found - return registration link
            return self.handle_user_not_found(email, request)

    def handle_active_user(self, user, request):
        """
        Handles the case for an active user requesting account action.

        For active users, this triggers the password reset flow by generating
        a reset token and sending a password reset email.

        Args:
            user: The CustomUser instance (active).
            request: The HTTP request object.

        Returns:
            Response: A success message indicating that an email has been sent.
        """
        frontend_url = settings.FRONTEND_URL

        PasswordResetToken.objects.filter(user=user).delete()
        reset_token = PasswordResetToken.objects.create(user=user)
        reset_link = self.build_reset_link(user, reset_token.token, frontend_url)

        self.send_active_account_email(user, reset_link, frontend_url)

        return Response({'message': 'Email sent. Please check your inbox.'}, status=status.HTTP_200_OK)

    def handle_inactive_user(self, user, request):
        """
        Handles the case for an inactive user requesting account action.

        For inactive users, this triggers the account activation flow by
        generating a new activation link and sending an activation email.

        Args:
            user: The CustomUser instance (inactive).
            request: The HTTP request object.

        Returns:
            Response: A success message indicating that an email has been sent.
        """
        frontend_url = settings.FRONTEND_URL

        activation_token = AccountActivationToken.objects.create(user=user)
        activation_link = request.build_absolute_uri(reverse('activate', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)), 'token': activation_token.token}))

        self.send_inactive_account_email(user, activation_link, frontend_url)

        return Response({'message': 'Email sent. Please check your inbox.'}, status=status.HTTP_200_OK)

    def handle_user_not_found(self, email, request):
        """
        Handles the case where no user is found for the provided email.

        Provides a registration link to allow users to register if their
        email is not found in the system.

        Args:
            email: The email address that was not found.
            request: The HTTP request object.

        Returns:
            Response: A response with a message indicating that the email was not
                      found and a registration URL.
        """
        frontend_url = settings.FRONTEND_URL
        register_url = f"{frontend_url}/register?email={email}"
        return Response({'message': 'Email address not found. You can register here.', 'register_url': register_url}, status=status.HTTP_404_NOT_FOUND)

    def build_reset_link(self, user, token, frontend_url):
        """
        Builds the password reset link. (Reused from PasswordResetRequestView)
        """
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"
        return reset_link

    def send_reset_email(self, user, reset_link, frontend_url):
        """
        Sends the password reset email. (Reused from PasswordResetRequestView, slightly adjusted comment)
        """
        mail_subject = 'Reset your Videoflix password'
        html_message = render_to_string('email_password_reset.html', {
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hello {user.username},
            please click on the following link to reset your password: {reset_link}
            If you did not request a password reset, please ignore this email.
            Thank you, The Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    def send_active_account_email(self, user, reset_link, frontend_url):
        """
        Sends an email for active accounts, typically with password reset link.
        """
        mail_subject = 'Videoflix Account Information'
        html_message = render_to_string('email_account_info_active.html', {
            'username': user.username,
            'reset_link': reset_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hello {user.username},
            Your Videoflix account is already active. If you have forgotten your password, click here: {reset_link}
            Thank you, The Videoflix Team
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
        """
        Sends an email for inactive accounts, typically with account activation link.
        """
        mail_subject = 'Activate your Videoflix Account'
        html_message = render_to_string('email-activate-account.html', {
            'username': user.username,
            'activation_link': activation_link,
            'frontend_url': frontend_url,
        })
        plain_message = f"""
            Hello {user.username},
            Please click on the link to activate your Videoflix account: {activation_link}
            Thank you, The Videoflix Team
        """
        email = EmailMessage(
            subject=mail_subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)