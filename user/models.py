import string
from random import choices

from django.core.exceptions import ValidationError
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
    birth_date = models.DateField(null=True, blank=True)
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


class GenderChoices(models.TextChoices):
    WOMEN = 'W', 'Women'
    MEN = 'M', 'Men'


class UserAdditional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='additional')
    gender_interested = models.CharField(max_length=10, choices=GenderChoices.choices)
    weight = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    shoulder_size = models.PositiveSmallIntegerField()  # cm
    chest_size = models.PositiveSmallIntegerField(null=True, blank=True)  # cm
    bust_size = models.PositiveSmallIntegerField(null=True, blank=True)  # cm
    waist_size = models.PositiveSmallIntegerField()  # cm
    hips_size = models.PositiveSmallIntegerField()  # cm
    inseam = models.PositiveSmallIntegerField()  # cm
    shoe_size = models.DecimalField(max_digits=3, decimal_places=1)  # standard US/CA shoe size

    @property
    def shirt_fits(self):
        return ShirtFit.objects.filter(user_additional=self)

    @property
    def trouser_fits(self):
        return TrouserFit.objects.filter(user_additional=self)

    def clean(self):
        if self.gender_interested == GenderChoices.MEN and not self.chest_size:
            raise ValidationError("Chest size should not be empty for men's clothing.")
        elif self.gender_interested == GenderChoices.WOMEN and not self.bust_size:
            raise ValidationError("Bust size should not be empty for women's clothing.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'id: {self.id}, user: {self.user.username}'


class ShirtFit(models.Model):
    class ShirtFitChoices(models.TextChoices):
        SLIM = 'Slim', 'Slim'
        REGULAR = 'Regular', 'Regular'

    user_additional = models.ForeignKey(UserAdditional, on_delete=models.CASCADE)
    fit_type = models.CharField(max_length=10, choices=ShirtFitChoices.choices)

    class Meta:
        unique_together = ('user_additional', 'fit_type')


class TrouserFit(models.Model):
    class TrouserFitChoices(models.TextChoices):
        SKINNY = 'Skinny', 'Skinny'
        SLIM = 'Slim', 'Slim'
        NORMAL = 'Normal', 'Normal'
        LOOSE = 'Loose', 'Loose'
        TAPERED = 'Tapered', 'Tapered'

    user_additional = models.ForeignKey(UserAdditional, on_delete=models.CASCADE)
    fit_type = models.CharField(max_length=10, choices=TrouserFitChoices.choices)

    class Meta:
        unique_together = ('user_additional', 'fit_type')


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
