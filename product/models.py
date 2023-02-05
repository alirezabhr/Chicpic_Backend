from django.db import models


class Category(models.Model):
    class GenderChoices(models.TextChoices):
        FEMALE = 'F', 'Female'
        MALE = 'M', 'Male'

    title = models.CharField(max_length=40)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
