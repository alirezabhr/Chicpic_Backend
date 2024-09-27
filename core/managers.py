from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None)

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def with_deleted(self):
        """Retrieve all records, including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_items(self):
        """Retrieve only soft-deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True).order_by('-deleted_at')
