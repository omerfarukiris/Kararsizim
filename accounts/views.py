from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import EmailAuthenticationForm, RegisterForm


def _safe_next(request):
    """`next` parametresi bu siteye aitse onu, değilse None döndürür."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return None


def register(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Hoş geldin @{user.username}! 🎉")
            return redirect(_safe_next(request) or settings.LOGIN_REDIRECT_URL)
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form, "next": _safe_next(request) or ""})


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Tekrar hoş geldin @{form.get_user().username}!")
        return response
