"""Oy veren kimliği (voter_key) ve sonuç hesaplama yardımcıları."""

import uuid

from django.conf import settings

from .models import Vote

VOTER_COOKIE = "kz_voter"
VOTER_COOKIE_SALT = "kararsizim.voter"
VOTER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 yıl


def _anonymous_id(request):
    """İmzalı `kz_voter` çerezindeki UUID'yi döndürür; yoksa/bozuksa None."""
    raw = request.get_signed_cookie(VOTER_COOKIE, default=None, salt=VOTER_COOKIE_SALT)
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None


def get_voter_key(request):
    """Mevcut oy veren anahtarı; misafirin çerezi yoksa None (yeni çerez üretmez)."""
    if request.user.is_authenticated:
        return f"u:{request.user.pk}"
    anon_id = _anonymous_id(request)
    return f"a:{anon_id}" if anon_id else None


def get_or_create_voter_key(request):
    """Oy kaydı için anahtarı döndürür.

    Dönüş: (voter_key, new_cookie_value). Misafirin geçerli çerezi yoksa yeni bir
    UUID üretilir ve `new_cookie_value` olarak döner; view bunu cevaba
    `set_voter_cookie` ile yazmalıdır. Diğer durumlarda `new_cookie_value` None'dır.
    """
    key = get_voter_key(request)
    if key:
        return key, None
    new_id = str(uuid.uuid4())
    return f"a:{new_id}", new_id


def set_voter_cookie(response, value):
    if value:
        response.set_signed_cookie(
            VOTER_COOKIE,
            value,
            salt=VOTER_COOKIE_SALT,
            max_age=VOTER_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
        )
    return response


def compute_results(poll, choices):
    """Seçenekler için oy sayısı, yüzde ve önde olma bilgisini hesaplar.

    `choices` her biri `vote_count` annotate edilmiş Choice nesneleridir.
    Toplam, seçenek oylarının toplamıdır (böylece yüzdeler ~%100 eder).
    """
    total = sum(choice.vote_count for choice in choices)
    top = max((choice.vote_count for choice in choices), default=0)
    results = []
    for choice in choices:
        percent = round(choice.vote_count * 100 / total, 1) if total else 0.0
        results.append(
            {
                "id": choice.pk,
                "text": choice.text,
                "order": choice.order,
                "votes": choice.vote_count,
                "percent": percent,
                "leader": top > 0 and choice.vote_count == top,
            }
        )
    return total, results


def attach_vote_state(polls, request):
    """Her ankete şablonun ihtiyaç duyduğu oy durumunu ekler.

    Ankete eklenen alanlar:
      - voted_choice_id: bu ziyaretçinin seçtiği seçenek (yoksa None)
      - can_vote: henüz oy vermediyse True
      - show_results: oy verdiyse ya da anketin sahibiyse True
      - results: compute_results çıktısı (her zaman hesaplanır; görünürlük şablonda)
    Anketlerin `choices` ilişkisi `vote_count` annotate edilerek prefetch edilmiş olmalı.
    """
    polls = list(polls)
    voter_key = get_voter_key(request)
    voted = {}
    if voter_key and polls:
        voted = dict(
            Vote.objects.filter(poll__in=polls, voter_key=voter_key).values_list("poll_id", "choice_id")
        )
    user_id = request.user.pk if request.user.is_authenticated else None

    for poll in polls:
        poll.voted_choice_id = voted.get(poll.pk)
        poll.can_vote = poll.voted_choice_id is None
        poll.show_results = not poll.can_vote or poll.author_id == user_id
        _, poll.results = compute_results(poll, list(poll.choices.all()))
        for row in poll.results:
            row["mine"] = row["id"] == poll.voted_choice_id
    return polls
