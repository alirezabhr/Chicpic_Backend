from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if the account is soft-deleted
        if get_user_model().objects.deleted_items().filter(pk=sociallogin.user.pk).exists():
            existed_user = sociallogin.account.user
            existed_user.restore()

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.is_verified = True
        return user
