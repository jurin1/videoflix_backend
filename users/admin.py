from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from rest_framework.authtoken.models import Token

class CustomUserAdmin(UserAdmin):
    """
    Admin interface for the CustomUser model.

    This class extends Django's built-in UserAdmin to customize the admin
    representation of the CustomUser model. It includes configurations for
    list display, fieldsets for editing and adding users, and a method to
    retrieve and display the user's authentication token.
    """
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'get_auth_token']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('adresse', 'telefon', 'profilbild')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('adresse', 'telefon', 'profilbild')}),
    )

    def get_auth_token(self, obj):
        """
        Retrieves or creates and returns the authentication token for a user.

        This method fetches the authentication token associated with the given
        CustomUser instance. If a token does not exist, it creates a new one.
        The token key is then returned for display in the admin list view.

        Args:
            obj: The CustomUser instance.

        Returns:
            str: The authentication token key for the user.
        """
        token, created = Token.objects.get_or_create(user=obj)
        return token.key


admin.site.register(CustomUser, CustomUserAdmin)