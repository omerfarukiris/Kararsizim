from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import PollForm
from .models import Choice, Poll, Vote
from .utils import attach_vote_state, compute_results, get_or_create_voter_key, set_voter_cookie

POLLS_PER_PAGE = 20


def member_required(message):
    """login_required gibi; misafiri girişe yönlendirirken bir uyarı mesajı da gösterir."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, message)
                return redirect_to_login(request.get_full_path())
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def poll_queryset():
    return (
        Poll.objects.select_related("author")
        .prefetch_related(
            Prefetch("choices", queryset=Choice.objects.annotate(vote_count=Count("votes")).order_by("order"))
        )
        .annotate(vote_count=Count("votes"))
        .order_by("-created_at")
    )


def paginate(request, queryset):
    return Paginator(queryset, POLLS_PER_PAGE).get_page(request.GET.get("sayfa"))


def home(request):
    page = paginate(request, poll_queryset())
    page.object_list = attach_vote_state(page.object_list, request)
    return render(request, "polls/home.html", {"page": page})


def poll_detail(request, pk):
    poll = get_object_or_404(poll_queryset(), pk=pk)
    attach_vote_state([poll], request)
    return render(request, "polls/detail.html", {"poll": poll})


def _wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _vote_payload(poll, voted_choice_id):
    choices = list(Choice.objects.filter(poll=poll).annotate(vote_count=Count("votes")).order_by("order"))
    total, results = compute_results(poll, choices)
    return {"total": total, "voted_choice_id": voted_choice_id, "results": results}


def _redirect_after_vote(request, poll):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("poll_detail", pk=poll.pk)


@require_POST
def vote(request, pk):
    """Oy kaydeder. fetch (Accept: application/json) için JSON, normal form için redirect döner."""
    poll = get_object_or_404(Poll, pk=pk)
    json_mode = _wants_json(request)

    choice = None
    choice_id = request.POST.get("choice", "")
    # isascii(): "²" gibi Unicode rakamlar isdigit() geçer ama int()'te patlar.
    if choice_id.isascii() and choice_id.isdigit():
        # Seçenek bu ankete ait olmalı; başka anketin seçeneği reddedilir.
        choice = Choice.objects.filter(pk=int(choice_id), poll=poll).first()
    if choice is None:
        message = "Geçersiz seçenek."
        if json_mode:
            return JsonResponse({"ok": False, "error": message}, status=400)
        messages.error(request, message)
        return _redirect_after_vote(request, poll)

    voter_key, new_cookie = get_or_create_voter_key(request)
    try:
        with transaction.atomic():
            Vote.objects.create(
                poll=poll,
                choice=choice,
                user=request.user if request.user.is_authenticated else None,
                voter_key=voter_key,
            )
    except IntegrityError:
        message = "Bu ankete zaten oy verdin."
        existing = Vote.objects.filter(poll=poll, voter_key=voter_key).values_list("choice_id", flat=True).first()
        if json_mode:
            return JsonResponse({"ok": False, "error": message, **_vote_payload(poll, existing)}, status=409)
        messages.info(request, message)
        return _redirect_after_vote(request, poll)

    if json_mode:
        response = JsonResponse({"ok": True, **_vote_payload(poll, choice.pk)})
    else:
        messages.success(request, "Oyun kaydedildi! 🗳️")
        response = _redirect_after_vote(request, poll)
    return set_voter_cookie(response, new_cookie)


@member_required("Anket oluşturmak için üye olmalısın.")
def poll_create(request):
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                poll = form.save(commit=False)
                poll.author = request.user
                poll.save()
                Choice.objects.bulk_create(
                    Choice(poll=poll, text=text, order=index)
                    for index, text in enumerate(form.cleaned_data["choices"])
                )
            messages.success(request, "Anketin yayında! 🎉")
            return redirect("poll_detail", pk=poll.pk)
    else:
        form = PollForm()

    return render(request, "polls/create.html", {"form": form})


@login_required
@require_POST
def poll_delete(request, pk):
    # Başkasının anketi için 404: anketin varlığı bile sızdırılmaz.
    poll = get_object_or_404(Poll, pk=pk, author=request.user)
    poll.delete()
    messages.success(request, "Anket silindi.")
    return redirect("my_polls")


@login_required
def my_polls(request):
    page = paginate(request, poll_queryset().filter(author=request.user))
    page.object_list = attach_vote_state(page.object_list, request)
    return render(request, "polls/my_polls.html", {"page": page})
