from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm

from .models import User


class AdminUserCreationForm(BaseUserCreationForm):
    """Admin panelinde yeni kullanıcı ekleme formu (özel User modeli için)."""

    class Meta:
        model = User
        fields = ("email", "username")


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
