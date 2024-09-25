from django.contrib import admin, messages
from user.models import User, DeletedUser, UserAdditional, ShirtFit, TrouserFit


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_verified', 'is_superuser', 'is_staff', 'date_joined', 'id')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('id', 'username', 'email', 'password', 'birth_date')}),
        ('Permissions', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'birth_date'),
        }),
    )

    filter_horizontal = ()
    readonly_fields = ('id', 'date_joined', 'last_login')


class DeletedUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'deleted_at', 'date_joined', 'id')
    search_fields = ('username', 'email')
    ordering = ('-deleted_at',)

    fieldsets = (
        (None, {'fields': ('id', 'username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_verified', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('date_joined', 'last_login', 'deleted_at')}),
    )

    readonly_fields = ('id', 'date_joined', 'last_login', 'deleted_at')

    def get_queryset(self, request):
        """Only display users that have been soft-deleted."""
        return self.model.objects.deleted_items()

    actions = ['restore_users']

    def restore_users(self, request, queryset):
        """Restore soft-deleted users."""
        for user in queryset:
            user.restore()  # Use the restore method from SoftDeleteModel
        self.message_user(request, f"{queryset.count()} user(s) restored successfully.", messages.SUCCESS)

    restore_users.short_description = "Restore selected users"

    def delete_model(self, request, obj):
        """Override the delete_model method to hard-delete users."""
        obj.hard_delete()
        self.message_user(request, f"User '{obj}' has been hard-deleted.", messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        """Override the delete_queryset method to hard-delete users."""
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f"{queryset.count()} user(s) have been hard-deleted.", messages.SUCCESS)



admin.site.register(User, UserAdmin)
admin.site.register(DeletedUser, DeletedUserAdmin)
admin.site.register(UserAdditional)
admin.site.register(ShirtFit)
admin.site.register(TrouserFit)
