from rest_framework.permissions import IsAuthenticated


class IsAdminOrSelf(IsAuthenticated):
    """
    Custom permission to allow only admin users or the user itself to access the view.
    """

    def has_object_permission(self, request, view, obj):
        # Allow access if the user is an admin
        if request.user.is_staff:
            return True

        return obj == request.user
