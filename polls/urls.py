from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("anket/yeni/", views.poll_create, name="poll_create"),
    path("anket/<int:pk>/", views.poll_detail, name="poll_detail"),
    path("anket/<int:pk>/oy/", views.vote, name="vote"),
    path("anket/<int:pk>/sil/", views.poll_delete, name="poll_delete"),
    path("anketlerim/", views.my_polls, name="my_polls"),
]
