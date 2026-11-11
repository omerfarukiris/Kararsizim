from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def time_ago(value):
    """'2 saat önce' gibi gösterir; bir dakikadan yeniyse 'az önce' der."""
    if not value:
        return ""
    if timezone.now() - value < timedelta(minutes=1):
        return "az önce"
    return f"{timesince(value)} önce"
