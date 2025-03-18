from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from users.models import CustomUser

class LoginTest(APITestCase):
    """
    Test suite for user login functionality.

    This class contains test cases to verify the user login process,
    including successful login with valid credentials and failed login
    attempts with invalid credentials.
    """

    def setUp(self):
        """
        Set up method to create a test user and define the login URL.

        This method is run before each test. It creates a user with a
        test email, username, and password, and it reverses the URL
        for the login endpoint to be used in the tests.
        """
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpassword'
        )
        self.login_url = reverse('login')

    def test_login_with_email_and_password_success(self):
        """
        Test successful login with valid email and password.

        This test case sends a POST request to the login URL with valid
        email and password credentials. It asserts that the response status
        code is HTTP 200 OK and that the response data contains an
        authentication token.
        """
        data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_with_invalid_email_fails(self):
        """
        Test failed login attempt with an invalid email.

        This test case sends a POST request to the login URL with an invalid
        email address and a valid password. It asserts that the response
        status code is HTTP 400 BAD REQUEST and that the response data
        contains a non_field_errors key, indicating a general error.
        """
        data = {
            'email': 'wrong@example.com',
            'password': 'testpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_with_invalid_password_fails(self):
        """
        Test failed login attempt with an invalid password.

        This test case sends a POST request to the login URL with a valid
        email address but an invalid password. It asserts that the response
        status code is HTTP 400 BAD REQUEST and that the response data
        contains a non_field_errors key, indicating a general error.
        """
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)