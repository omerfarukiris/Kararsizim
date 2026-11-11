from django.contrib import admin
from django.db.models import Count

from .models import Choice, Poll, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    max_num = 5
    min_num = 2
    validate_min = True
    validate_max = True


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "author", "created_at", "vote_count")
    list_select_related = ("author",)
    search_fields = ("question", "author__username")
    inlines = [ChoiceInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(vote_count=Count("votes"))

    @admin.display(description="oy", ordering="vote_count")
    def vote_count(self, obj):
        return obj.vote_count


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("poll", "choice", "voter_key", "user", "created_at")
    list_select_related = ("poll", "choice", "user")
    search_fields = ("voter_key", "poll__question")
    autocomplete_fields = ("poll", "user")
    raw_id_fields = ("choice",)
