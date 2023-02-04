from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
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
