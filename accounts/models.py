from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower

username_validator = RegexValidator(
    regex=r"^[A-Za-z0-9_.]+$",
    message="Kullanıcı adı yalnızca harf, rakam, alt çizgi (_) ve nokta (.) içerebilir.",
)


class UserManager(BaseUserManager):
    """E-posta ile giriş yapan kullanıcılar için yönetici."""

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("E-posta zorunludur.")
        if not username:
            raise ValueError("Kullanıcı adı zorunludur.")
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser için is_staff=True olmalı.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser için is_superuser=True olmalı.")
        return self._create_user(email, username, password, **extra_fields)

    def get_by_natural_key(self, email):
        # Giriş sırasında e-posta büyük/küçük harf duyarsız eşleşsin.
        return self.get(email__iexact=email)


class User(AbstractUser):
    email = models.EmailField(
        "e-posta",
        unique=True,
        error_messages={"unique": "Bu e-posta zaten kayıtlı."},
    )
    username = models.CharField(
        "kullanıcı adı",
        max_length=30,
        unique=True,
        validators=[MinLengthValidator(3), username_validator],
        help_text="3–30 karakter; harf, rakam, _ ve . kullanılabilir.",
        error_messages={"unique": "Bu kullanıcı adı alınmış."},
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        verbose_name = "kullanıcı"
        verbose_name_plural = "kullanıcılar"
        constraints = [
            models.UniqueConstraint(
                Lower("username"),
                name="unique_username_ci",
                violation_error_message="Bu kullanıcı adı alınmış.",
            ),
            models.UniqueConstraint(
                Lower("email"),
                name="unique_email_ci",
                violation_error_message="Bu e-posta zaten kayıtlı.",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.username:
            self.username = self.username.strip()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()

    def __str__(self):
        return f"@{self.username}"
