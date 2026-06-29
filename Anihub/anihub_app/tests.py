import json
import time
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model, get_user
from anihub_app.auth import AuthTokenService

User = get_user_model()

class TestAuthTokenService(TestCase):
    def setUp(self):
        self.token_service = AuthTokenService()
        self.user_id = 42

    def test_generate_and_validate_token(self):
        # Generate token
        token = self.token_service.generate_token(self.user_id)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        # Validate token
        payload = self.token_service.validate_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("user_id"), self.user_id)
        self.assertGreater(payload.get("exp"), time.time())

    def test_expired_token(self):
        # Generate a token with a negative expiration (expired in the past)
        token = self.token_service.generate_token(self.user_id, expiration_seconds=-10)
        self.assertIsNotNone(token)

        # Validate token should return None
        payload = self.token_service.validate_token(token)
        self.assertIsNone(payload)

    def test_invalid_token_format(self):
        # Validate random string
        payload = self.token_service.validate_token("invalid_token_string")
        self.assertIsNone(payload)

        # Validate empty string
        payload = self.token_service.validate_token("")
        self.assertIsNone(payload)

    def test_tampered_token(self):
        # Generate a valid token
        token = self.token_service.generate_token(self.user_id)
        
        # Tamper it by replacing some characters
        if ":" in token:
            iv, ct = token.split(":")
            # Alter the ciphertext
            tampered_ct = ct[:-2] + "AA"
            tampered_token = f"{iv}:{tampered_ct}"
        else:
            tampered_token = token[:-2] + "AA"

        payload = self.token_service.validate_token(tampered_token)
        self.assertIsNone(payload)


class TestTokenRequiredDecorator(TestCase):
    def setUp(self):
        self.token_service = AuthTokenService()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="testuser@example.com"
        )
        self.token = self.token_service.generate_token(self.user.id)
        self.url = reverse("api_catalog")

    @patch("anihub_app.views.JikanAdapter.get_anime_catalog")
    def test_valid_token(self, mock_get_anime_catalog):
        mock_get_anime_catalog.return_value = [{"title": "Death Note"}]
        
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        response = self.client.get(self.url, **headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("catalog", data)
        self.assertEqual(data["catalog"], [{"title": "Death Note"}])
        mock_get_anime_catalog.assert_called_once()

    def test_missing_auth_header(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

    def test_malformed_auth_header(self):
        # Header present but does not start with Bearer
        headers = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

        # Header has Bearer but lacks token
        headers = {"HTTP_AUTHORIZATION": "Bearer"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

    def test_invalid_token(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer invalidtoken123"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Invalid or expired token"})


class TestLoginView(TestCase):
    def setUp(self):
        self.login_url = reverse("login")
        self.username = "testuser"
        self.password = "securepassword123"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testuser@example.com"
        )

    def test_login_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/login.html")
        self.assertIn("form", response.context)

    def test_login_post_success(self):
        # Log in with correct credentials
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": self.password
        })
        # Check redirection to 'home'
        self.assertRedirects(response, reverse("home"))
        
        # Check if the user is authenticated in the session
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, self.username)

    def test_login_post_failure(self):
        # Log in with incorrect credentials
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/login.html")
        self.assertIn("form", response.context)
        
        # Check that the form in context has validation errors
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        
        # Check that the user is not authenticated in the session
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
