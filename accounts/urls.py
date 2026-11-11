from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("kayit/", views.register, name="register"),
    path("giris/", views.EmailLoginView.as_view(), name="login"),
    # Django 5'te LogoutView yalnızca POST kabul eder.
    path("cikis/", LogoutView.as_view(), name="logout"),
]
