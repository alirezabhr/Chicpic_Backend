from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import OTP
from mail_service.service import EmailService


@receiver(post_save, sender=OTP)
def send_otp_via_email(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        code = instance.code
        EmailService.send_otp(user=user, code=code)
