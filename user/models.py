import string
from random import choices

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .managers import CustomUserManager
from .validators import CustomUsernameValidator


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    username_validator = CustomUsernameValidator()

    email = models.EmailField(max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True, validators=[username_validator])
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    groups = None
    user_permissions = None

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def tokens(self):
        tokens = RefreshToken.for_user(self)
        return {
            'access': str(tokens.access_token),
            'refresh': str(tokens),
        }

    def __str__(self):
        return self.username


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField()

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'One Time Password'
        verbose_name_plural = 'One Time Passwords'

    @classmethod
    def generate_otp(cls, user):
        code = ''.join(choices(string.digits, k=6))
        expire_at = timezone.now() + timezone.timedelta(minutes=10)
        return cls.objects.create(user=user, code=code, expire_at=expire_at)
