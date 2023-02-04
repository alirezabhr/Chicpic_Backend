from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from .service import EmailService

User = get_user_model()


class EmailServiceTests(TestCase):
    def test_send_simple_email(self):
        # Arrange
        subject = "Test Subject"
        body = "Test Body"
        to = ["test1@example.com", "test2@example.com"]

        # Act
        EmailService.send_simple_email(subject, body, to)

        # Assert
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].to, to)

    def test_send_email_to_admins(self):
        # Arrange
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        subject = "Test Subject"
        body = "Test Body"

        # Act
        EmailService.send_email_to_admins(subject, body)

        # Assert
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].to, ['admin@example.com'])

    def test_send_otp(self):
        # Arrange
        user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='password'
        )
        code = '123456'

        # Act
        EmailService.send_otp(user, code)

        # Assert
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your account")
        self.assertIn(f"Your verification code is:\n{code}", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['test_user@example.com'])
