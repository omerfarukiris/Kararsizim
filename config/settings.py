"""Kararsızım — Django ayarları.

Gizli bilgiler ve ortama göre değişen her şey ortam değişkenlerinden okunur.
Lokal geliştirmede proje kökündeki `.env` dosyası otomatik yüklenir.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Temel -------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-sadece-lokal-gelistirme-icin"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY ortam değişkeni tanımlı olmalı.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Vercel her deploy'a kendi adresini verir (VERCEL_URL, VERCEL_BRANCH_URL); Vercel'in
# deploy sonrası kontrolleri ve preview'lar bu adreslere gelir. Joker yerine yalnızca bunlar.
for _vercel_host in (os.environ.get("VERCEL_URL"), os.environ.get("VERCEL_BRANCH_URL")):
    if _vercel_host and _vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_vercel_host)
# Aynı adresten gelen formlar için gerekmez (Django Origin'i Host ile karşılaştırır).
# Yalnızca başka bir kökenden POST kabul edilecekse doldurulur; joker (*.vercel.app)
# kullanmaktan kaçın — Vercel'deki herkesin sitesini güvenilir sayar.
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")


# --- Uygulamalar ------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "polls",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Veritabanı -------------------------------------------------------------
# DATABASE_URL boşsa SQLite, doluysa Postgres (Supabase transaction pooler, port 6543).
# Migration'lar için session pooler (port 5432) kullanmak üzere:
#   DJANGO_DB_DIRECT=1 python manage.py migrate
# Bu durumda DATABASE_URL_DIRECT okunur.

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if env_bool("DJANGO_DB_DIRECT"):
    DATABASE_URL = os.environ.get("DATABASE_URL_DIRECT", "").strip()
    if not DATABASE_URL:
        raise ImproperlyConfigured("DJANGO_DB_DIRECT=1 için DATABASE_URL_DIRECT tanımlı olmalı.")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            ssl_require=True,
        )
    }
    # Supabase transaction pooler (port 6543) server-side cursor desteklemez.
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Kimlik doğrulama -------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/giris/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# --- Dil ve zaman -----------------------------------------------------------

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True


# --- Statik dosyalar --------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Hash'li/sıkıştırılmış dosyalar `collectstatic` gerektirir; bu yüzden yalnızca
# production'da (DEBUG=False) kullanılır. Lokal geliştirme ve testler sade depolama ile çalışır.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
# Manifest'te olmayan bir dosya istenirse hata fırlatmak yerine hash'siz adı kullan;
# aksi halde tek bir eksik dosya tüm sayfaları (500 sayfası dahil) çökertir.
WHITENOISE_MANIFEST_STRICT = False


# --- Güvenlik (production) --------------------------------------------------

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Vercel HTTPS'i proxy'de sonlandırır; gerçek protokol bu başlıktan okunur.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    # HSTS: tarayıcı siteyi bir süre yalnızca HTTPS ile açar. Kısa başlatıldı;
    # her şey yolundaysa DJANGO_HSTS_SECONDS=31536000 (1 yıl) yapılabilir.
    # includeSubDomains/preload bilerek kapalı (geri alınması zor).
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
