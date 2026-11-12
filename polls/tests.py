from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Choice, Poll, Vote

PASSWORD = "Gizli-Parola-987"


def make_user(username="ali"):
    return User.objects.create_user(email=f"{username}@ornek.com", username=username, password=PASSWORD)


def make_poll(author, question="Sinema mı restoran mı?", choices=("Sinema", "Restoran")):
    poll = Poll.objects.create(author=author, question=question)
    for i, text in enumerate(choices):
        Choice.objects.create(poll=poll, text=text, order=i)
    return poll


class PollCreateTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.url = reverse("poll_create")

    def post(self, choices, question="Bu akşam ne yapsam?", description=""):
        return self.client.post(self.url, {"question": question, "description": description, "choices": choices})

    def test_create_valid_poll(self):
        response = self.post(["  Sinema ", "Restoran", "", "Evde kal"], description="Hava güzel")
        poll = Poll.objects.get()
        self.assertRedirects(response, reverse("poll_detail", args=[poll.pk]))
        self.assertEqual(poll.author, self.user)
        self.assertEqual(
            list(poll.choices.values_list("text", "order")),
            [("Sinema", 0), ("Restoran", 1), ("Evde kal", 2)],
        )

    def test_one_choice_rejected(self):
        response = self.post(["Sinema", "", ""])
        self.assertContains(response, "En az 2 seçenek girmelisin.")
        self.assertFalse(Poll.objects.exists())

    def test_six_choices_rejected(self):
        response = self.post(["A1", "B2", "C3", "D4", "E5", "F6"])
        self.assertContains(response, "En fazla 5 seçenek ekleyebilirsin.")
        self.assertFalse(Poll.objects.exists())

    def test_five_choices_allowed(self):
        self.post(["A1", "B2", "C3", "D4", "E5"])
        self.assertEqual(Poll.objects.get().choices.count(), 5)

    def test_duplicate_choices_rejected_case_insensitive(self):
        response = self.post(["Sinema", "  SINEMA  ", "Restoran"])
        self.assertContains(response, "Aynı seçeneği iki kez yazamazsın.")
        self.assertFalse(Poll.objects.exists())

    def test_short_question_rejected(self):
        response = self.post(["Sinema", "Restoran"], question="  ab ")
        self.assertContains(response, "Soru en az 5 karakter olmalı.")
        self.assertFalse(Poll.objects.exists())

    def test_too_long_choice_rejected(self):
        response = self.post(["x" * 101, "Restoran"])
        self.assertContains(response, "en fazla 100 karakter")
        self.assertFalse(Poll.objects.exists())

    def test_form_keeps_values_after_error(self):
        response = self.post(["Sinema", ""])
        self.assertContains(response, 'value="Sinema"')


class GuestAccessTests(TestCase):
    def setUp(self):
        self.poll = make_poll(make_user())

    def test_guest_can_see_home_and_detail(self):
        self.assertContains(self.client.get(reverse("home")), "Sinema mı restoran mı?")
        response = self.client.get(reverse("poll_detail", args=[self.poll.pk]))
        self.assertContains(response, "@ali")
        self.assertNotContains(response, "ali@ornek.com")

    def test_guest_redirected_from_create_with_message(self):
        response = self.client.get(reverse("poll_create"), follow=True)
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('poll_create')}")
        self.assertContains(response, "Anket oluşturmak için üye olmalısın.")

    def test_guest_post_to_create_does_not_create(self):
        self.client.post(reverse("poll_create"), {"question": "Misafir sorusu", "choices": ["A", "B"]})
        self.assertEqual(Poll.objects.count(), 1)

    def test_login_returns_to_create_form(self):
        response = self.client.post(
            f"{reverse('login')}?next={reverse('poll_create')}",
            {"username": "ali@ornek.com", "password": PASSWORD, "next": reverse("poll_create")},
        )
        self.assertRedirects(response, reverse("poll_create"))

    def test_guest_sees_create_button(self):
        self.assertContains(self.client.get(reverse("home")), "+ Anket Oluştur")

    def test_missing_poll_404(self):
        self.assertEqual(self.client.get(reverse("poll_detail", args=[999])).status_code, 404)


class PollDeleteTests(TestCase):
    def setUp(self):
        self.owner = make_user("sahip")
        self.other = make_user("baska")
        self.poll = make_poll(self.owner)
        self.url = reverse("poll_delete", args=[self.poll.pk])

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertTrue(Poll.objects.filter(pk=self.poll.pk).exists())

    def test_guest_cannot_delete(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Poll.objects.filter(pk=self.poll.pk).exists())

    def test_delete_requires_post(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(Poll.objects.filter(pk=self.poll.pk).exists())

    def test_owner_can_delete(self):
        self.client.force_login(self.owner)
        self.assertRedirects(self.client.post(self.url), reverse("my_polls"))
        self.assertFalse(Poll.objects.exists())
        self.assertFalse(Choice.objects.exists())

    def test_delete_button_only_for_owner(self):
        detail = reverse("poll_detail", args=[self.poll.pk])
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(detail), self.url)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(detail), self.url)


class ListingTests(TestCase):
    def test_home_paginates_20_newest_first(self):
        user = make_user()
        for i in range(25):
            make_poll(user, question=f"Anket numarası {i}")
        page1 = self.client.get(reverse("home"))
        self.assertEqual(len(page1.context["page"].object_list), 20)
        self.assertEqual(page1.context["page"].object_list[0].question, "Anket numarası 24")
        page2 = self.client.get(reverse("home") + "?sayfa=2")
        self.assertEqual(len(page2.context["page"].object_list), 5)

    def test_empty_state(self):
        self.assertContains(self.client.get(reverse("home")), "İlk anketi sen oluştur")

    def test_my_polls_shows_only_own(self):
        me, other = make_user("ben"), make_user("o")
        make_poll(me, question="Benim anketim")
        make_poll(other, question="Onun anketi")
        self.client.force_login(me)
        response = self.client.get(reverse("my_polls"))
        self.assertContains(response, "Benim anketim")
        self.assertNotContains(response, "Onun anketi")

    def test_my_polls_requires_login(self):
        response = self.client.get(reverse("my_polls"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my_polls')}")


class VoteTests(TestCase):
    def setUp(self):
        self.owner = make_user("sahip")
        self.poll = make_poll(self.owner, choices=("Sinema", "Restoran", "Evde kal"))
        self.sinema, self.restoran, self.evde = self.poll.choices.all()
        self.url = reverse("vote", args=[self.poll.pk])
        self.detail = reverse("poll_detail", args=[self.poll.pk])

    def vote_json(self, choice, client=None):
        return (client or self.client).post(self.url, {"choice": choice.pk}, HTTP_ACCEPT="application/json")

    def test_guest_vote_json_sets_cookie(self):
        response = self.vote_json(self.sinema)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["voted_choice_id"], self.sinema.pk)
        self.assertEqual([r["id"] for r in data["results"]], [self.sinema.pk, self.restoran.pk, self.evde.pk])
        self.assertIn("kz_voter", response.cookies)
        vote = Vote.objects.get()
        self.assertTrue(vote.voter_key.startswith("a:"))
        self.assertIsNone(vote.user)

    def test_guest_second_vote_rejected(self):
        self.vote_json(self.sinema)
        response = self.vote_json(self.restoran)
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data["error"], "Bu ankete zaten oy verdin.")
        self.assertEqual(data["voted_choice_id"], self.sinema.pk)
        self.assertEqual(Vote.objects.count(), 1)

    def test_member_vote_and_second_attempt(self):
        voter = make_user("uye")
        self.client.force_login(voter)
        self.assertEqual(self.vote_json(self.restoran).status_code, 200)
        vote = Vote.objects.get()
        self.assertEqual(vote.voter_key, f"u:{voter.pk}")
        self.assertEqual(vote.user, voter)
        response = self.vote_json(self.sinema)
        self.assertEqual(response.json()["error"], "Bu ankete zaten oy verdin.")

    def test_form_post_without_js(self):
        response = self.client.post(self.url, {"choice": self.evde.pk}, follow=True)
        self.assertRedirects(response, self.detail)
        self.assertContains(response, "Oyun kaydedildi!")
        response = self.client.post(self.url, {"choice": self.sinema.pk}, follow=True)
        self.assertContains(response, "Bu ankete zaten oy verdin.")
        self.assertEqual(Vote.objects.count(), 1)

    def test_form_post_redirects_to_safe_next(self):
        response = self.client.post(self.url, {"choice": self.evde.pk, "next": "/?sayfa=2#anket-1"})
        self.assertRedirects(response, "/?sayfa=2#anket-1", fetch_redirect_response=False)
        response = self.client.post(self.url, {"choice": self.evde.pk, "next": "https://kotu.example.com/"})
        self.assertRedirects(response, self.detail)

    def test_choice_from_other_poll_rejected(self):
        other = make_poll(self.owner, question="Başka bir anket")
        response = self.client.post(self.url, {"choice": other.choices.first().pk}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Geçersiz seçenek.")
        self.assertFalse(Vote.objects.exists())

    def test_invalid_choice_values_rejected(self):
        for value in ["", "abc", "999999", "²", "-1", "1.5"]:
            response = self.client.post(self.url, {"choice": value}, HTTP_ACCEPT="application/json")
            self.assertEqual(response.status_code, 400)
        self.assertFalse(Vote.objects.exists())

    def test_vote_requires_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_tampered_cookie_gets_new_key(self):
        self.client.cookies["kz_voter"] = "sahte-deger"
        self.assertEqual(self.vote_json(self.sinema).status_code, 200)
        self.assertNotEqual(Vote.objects.get().voter_key, "a:sahte-deger")

    def test_percentages_sum_to_about_100(self):
        for i, choice in enumerate([self.sinema, self.sinema, self.restoran, self.evde, self.evde, self.evde]):
            Vote.objects.create(poll=self.poll, choice=choice, voter_key=f"a:test-{i}")
        data = self.vote_json(self.restoran).json()
        self.assertEqual(data["total"], 7)
        self.assertAlmostEqual(sum(r["percent"] for r in data["results"]), 100, delta=0.2)
        leaders = [r["id"] for r in data["results"] if r["leader"]]
        self.assertEqual(leaders, [self.evde.pk])

    def test_json_never_contains_email(self):
        self.client.force_login(make_user("uye"))
        self.assertNotIn("@ornek.com", self.vote_json(self.sinema).content.decode())


class ResultVisibilityTests(TestCase):
    def setUp(self):
        self.owner = make_user("sahip")
        self.poll = make_poll(self.owner)
        self.sinema = self.poll.choices.get(order=0)
        self.detail = reverse("poll_detail", args=[self.poll.pk])
        Vote.objects.create(poll=self.poll, choice=self.sinema, voter_key="a:baskasi")

    def test_non_voter_sees_buttons_not_results(self):
        for url in [self.detail, reverse("home")]:
            response = self.client.get(url)
            self.assertContains(response, 'name="choice"')
            self.assertNotContains(response, "data-results")
            self.assertContains(response, "Sonuçları görmek için oy ver.")
            self.assertContains(response, '<span data-total>1</span> oy', html=False)

    def test_voter_sees_results_after_refresh(self):
        self.client.post(reverse("vote", args=[self.poll.pk]), {"choice": self.sinema.pk})
        for url in [self.detail, reverse("home")]:
            response = self.client.get(url)
            self.assertContains(response, "data-results")
            self.assertNotContains(response, 'name="choice"')
            self.assertContains(response, "✓ senin oyun")
            self.assertContains(response, "%100,0 · 2 oy")

    def test_owner_always_sees_results_and_can_vote(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.detail)
        self.assertContains(response, "data-results")
        self.assertContains(response, 'name="choice"')
        self.assertNotContains(response, "✓ senin oyun")

    def test_member_vote_state_not_shared_with_guest_cookie(self):
        member = make_user("uye")
        self.client.force_login(member)
        self.client.post(reverse("vote", args=[self.poll.pk]), {"choice": self.sinema.pk})
        self.client.logout()
        self.assertContains(self.client.get(self.detail), 'name="choice"')


class ErrorPageTests(TestCase):
    def test_custom_404_page(self):
        response = self.client.get("/yok-boyle-sayfa/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Ana sayfaya dön", status_code=404)
        self.assertNotContains(response, "Traceback", status_code=404)

    def test_500_template_renders_without_context(self):
        from django.template.loader import render_to_string

        html = render_to_string("500.html")
        self.assertIn("Bir şeyler ters gitti.", html)
