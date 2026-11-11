from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator
from django.db import models

MIN_CHOICES = 2
MAX_CHOICES = 5


class Poll(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="polls",
        verbose_name="sahibi",
    )
    question = models.CharField("soru", max_length=200, validators=[MinLengthValidator(5)])
    description = models.TextField("açıklama", blank=True, validators=[MaxLengthValidator(500)])
    created_at = models.DateTimeField("oluşturulma", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "anket"
        verbose_name_plural = "anketler"

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        # Listelerde `annotate(vote_count=Count("votes"))` varsa onu kullan.
        annotated = getattr(self, "vote_count", None)
        if annotated is not None:
            return annotated
        return self.votes.count()


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices", verbose_name="anket")
    text = models.CharField("seçenek", max_length=100)
    order = models.PositiveSmallIntegerField("sıra", default=0, validators=[MaxValueValidator(MAX_CHOICES - 1)])

    class Meta:
        ordering = ["order"]
        verbose_name = "seçenek"
        verbose_name_plural = "seçenekler"
        constraints = [
            models.UniqueConstraint(fields=["poll", "order"], name="unique_choice_order_per_poll"),
        ]

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes", verbose_name="anket")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name="votes", verbose_name="seçenek")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="votes",
        verbose_name="kullanıcı",
    )
    # Üye: "u:<user.id>", misafir: "a:<uuid>" — bkz. polls/utils.py
    voter_key = models.CharField("oy veren anahtarı", max_length=64)
    created_at = models.DateTimeField("oy zamanı", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "oy"
        verbose_name_plural = "oylar"
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "voter_key"],
                name="one_vote_per_voter",
                violation_error_message="Bu ankete zaten oy verdin.",
            ),
        ]

    def __str__(self):
        return f"{self.voter_key} → {self.choice}"

    def clean(self):
        super().clean()
        if self.poll_id and self.choice_id and self.choice.poll_id != self.poll_id:
            raise ValidationError({"choice": "Seçenek bu ankete ait değil."})
