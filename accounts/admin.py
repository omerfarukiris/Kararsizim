from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = ("username", "email", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Yetkiler", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Tarihler", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2"),
        }),
    )
