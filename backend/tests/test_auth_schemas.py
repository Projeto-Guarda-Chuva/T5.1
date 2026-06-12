import unittest

from pydantic import ValidationError

from app.schemas.admin import AdminCreateRequest
from app.schemas.auth import GoogleLoginRequest, LoginRequest, RegisterRequest
from app.schemas.change_password import ChangePasswordRequest
from app.schemas.password_recovery import ForgotPasswordRequest, ResetPasswordRequest


class AuthSchemaTests(unittest.TestCase):
    def test_change_password_accepts_matching_passwords(self) -> None:
        payload = ChangePasswordRequest(
            current_password="senha-antiga",
            new_password="nova123",
            new_password_confirmation="nova123",
        )

        self.assertEqual(payload.new_password, "nova123")

    def test_change_password_rejects_mismatched_confirmation(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ChangePasswordRequest(
                current_password="senha-antiga",
                new_password="nova123",
                new_password_confirmation="diferente",
            )

        self.assertIn("As senhas não coincidem.", str(context.exception))

    def test_reset_password_requires_minimum_length(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ResetPasswordRequest(
                email="user@example.com",
                code="ABC12345",
                password="123",
                password_confirmation="123",
            )

        self.assertIn("at least 6 characters", str(context.exception))

    def test_admin_create_rejects_mismatched_confirmation(self) -> None:
        with self.assertRaises(ValidationError) as context:
            AdminCreateRequest(
                name="Admin",
                email="admin@example.com",
                password="segredo1",
                password_confirmation="segredo2",
            )

        self.assertIn("As senhas não coincidem.", str(context.exception))

    def test_login_request_requires_non_empty_password(self) -> None:
        with self.assertRaises(ValidationError) as context:
            LoginRequest(email="admin@example.com", password="")

        self.assertIn("at least 1 character", str(context.exception))

    def test_register_request_normalizes_email_validation(self) -> None:
        payload = RegisterRequest(
            nome="Gabriel",
            email="gabriel@example.com",
            password="segredo123",
        )

        self.assertEqual(payload.email, "gabriel@example.com")

    def test_google_login_requires_credential(self) -> None:
        with self.assertRaises(ValidationError) as context:
            GoogleLoginRequest(credential="")

        self.assertIn("at least 1 character", str(context.exception))

    def test_forgot_password_requires_valid_email(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ForgotPasswordRequest(email="email-invalido")

        self.assertIn("email address", str(context.exception).lower())
