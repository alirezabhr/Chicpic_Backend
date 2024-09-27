from django.db import models
from django.utils import timezone

from core.managers import SoftDeleteManager


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
