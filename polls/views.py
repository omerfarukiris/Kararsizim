from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PollForm
from .models import Choice, Poll

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
        .prefetch_related("choices")
        .annotate(vote_count=Count("votes"))
        .order_by("-created_at")
    )


def paginate(request, queryset):
    return Paginator(queryset, POLLS_PER_PAGE).get_page(request.GET.get("sayfa"))


def home(request):
    page = paginate(request, poll_queryset())
    return render(request, "polls/home.html", {"page": page})


def poll_detail(request, pk):
    poll = get_object_or_404(poll_queryset(), pk=pk)
    return render(request, "polls/detail.html", {"poll": poll})


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
    return render(request, "polls/my_polls.html", {"page": page})
