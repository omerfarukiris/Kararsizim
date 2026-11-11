from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "Gizli-Parola-987"


def register_data(**overrides):
    data = {
        "email": "ali@ornek.com",
        "username": "ali",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(overrides)
    return data


class RegisterTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(reverse("register"), register_data(email="Ali@Ornek.COM"))
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="ali")
        self.assertEqual(user.email, "ali@ornek.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_respects_safe_next(self):
        response = self.client.post(reverse("register") + "?next=/admin/", register_data())
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)

    def test_register_ignores_external_next(self):
        response = self.client.post(reverse("register"), register_data(next="https://kotu.example.com/"))
        self.assertRedirects(response, reverse("home"))

    def test_duplicate_email_any_case_rejected(self):
        User.objects.create_user(email="ali@ornek.com", username="ali", password=PASSWORD)
        response = self.client.post(reverse("register"), register_data(email="ALI@ornek.com", username="veli"))
        self.assertContains(response, "Bu e-posta zaten kayıtlı.")
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_any_case_rejected(self):
        User.objects.create_user(email="ali@ornek.com", username="Ali", password=PASSWORD)
        response = self.client.post(reverse("register"), register_data(email="baska@ornek.com", username="aLI"))
        self.assertContains(response, "Bu kullanıcı adı alınmış.")
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_username_and_password_mismatch(self):
        response = self.client.post(
            reverse("register"), register_data(username="a b!", password2="baska-parola-123")
        )
        self.assertContains(response, "Kullanıcı adı yalnızca harf, rakam")
        self.assertContains(response, "Parolalar birbiriyle eşleşmiyor.")
        self.assertFalse(User.objects.exists())

    def test_authenticated_user_redirected_from_register(self):
        user = User.objects.create_user(email="ali@ornek.com", username="ali", password=PASSWORD)
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("register")), reverse("home"))


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="ali@ornek.com", username="ali", password=PASSWORD)

    def test_login_with_email_case_insensitive(self):
        response = self.client.post(reverse("login"), {"username": "ALI@ornek.com", "password": PASSWORD})
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_wrong_password(self):
        response = self.client.post(reverse("login"), {"username": "ali@ornek.com", "password": "yanlis"})
        self.assertContains(response, "E-posta veya parola hatalı.")

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class NavbarPrivacyTests(TestCase):
    def test_navbar_shows_username_not_email(self):
        user = User.objects.create_user(email="gizli@ornek.com", username="ali", password=PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "@ali")
        self.assertNotContains(response, "gizli@ornek.com")
        self.assertContains(response, "Çıkış")

    def test_navbar_guest_links(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Giriş")
        self.assertContains(response, "Kayıt Ol")
