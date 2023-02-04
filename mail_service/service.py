from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.conf import settings

User = get_user_model()


class EmailService:
    @staticmethod
    def send_mail(email: EmailMessage):
        tmp_email_backend = settings.EMAIL_BACKEND

        if settings.DEBUG:
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

        try:
            email.send()
        except Exception as exc:
            raise exc
        finally:
            settings.EMAIL_BACKEND = tmp_email_backend

    @staticmethod
    def send_simple_email(subject: str, body: str, to: list):
        email = EmailMessage(
            subject=subject,
            body=body,
            to=to
        )
        EmailService.send_mail(email)

    @staticmethod
    def send_email_to_admins(subject: str, body: str):
        user_model = User
        admins = user_model.objects.filter(is_superuser=True)
        admin_emails = list(map(lambda admin: admin.email, admins))

        email = EmailMessage(
            subject=subject,
            body=body,
            to=admin_emails
        )
        EmailService.send_mail(email)

    @staticmethod
    def send_otp(user: User, code: str):
        normalized_email = User.objects.normalize_email(user.email)
        email_body = f"Hi {user.username},\n\nYour verification code is:\n{code}"
        EmailService.send_simple_email(
            subject='Verify your account',
            body=email_body,
            to=[normalized_email]
        )
