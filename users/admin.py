from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from rest_framework.authtoken.models import Token

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'get_auth_token']

    fieldsets = UserAdmin.fieldsets + (
        ('Zusätzliche Informationen', {'fields': ('adresse', 'telefon', 'profilbild')}), 
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('adresse', 'telefon', 'profilbild')}), 
    )

    def get_auth_token(self, obj):
        token, created = Token.objects.get_or_create(user=obj)
        return token.key


admin.site.register(CustomUser, CustomUserAdmin)

