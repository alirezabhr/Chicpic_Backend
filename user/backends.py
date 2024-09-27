from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()


class EmailUsernameAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Authenticate user by username or email even if the user is soft deleted
            user = User.objects.with_deleted().get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            # Restore the user if the user is soft deleted
            if user.is_deleted:
                user.restore()
            return user

        return None
