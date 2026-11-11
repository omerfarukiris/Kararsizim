from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm, UserChangeForm

from .models import User


class RegisterForm(BaseUserCreationForm):
    """Kayıt formu: e-posta, kullanıcı adı, parola x2."""

    error_messages = {
        "password_mismatch": "Parolalar birbiriyle eşleşmiyor.",
    }

    class Meta:
        model = User
        fields = ("email", "username")
        labels = {"email": "E-posta", "username": "Kullanıcı adı"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "autofocus": True})
        self.fields["username"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password1"].label = "Parola"
        self.fields["password2"].label = "Parola (tekrar)"
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu e-posta zaten kayıtlı.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı alınmış.")
        return username


class EmailAuthenticationForm(AuthenticationForm):
    """E-posta + parola ile giriş."""

    error_messages = {
        "invalid_login": "E-posta veya parola hatalı.",
        "inactive": "Bu hesap aktif değil.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"] = forms.EmailField(
            label="E-posta",
            widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
        )
        self.fields["password"].label = "Parola"


class AdminUserCreationForm(BaseUserCreationForm):
    """Admin panelinde yeni kullanıcı ekleme formu (özel User modeli için)."""

    class Meta:
        model = User
        fields = ("email", "username")


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
