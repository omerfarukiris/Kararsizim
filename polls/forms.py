from django import forms

from .models import MAX_CHOICES, MIN_CHOICES, Choice, Poll

CHOICE_MAX_LENGTH = Choice._meta.get_field("text").max_length


class ChoiceListWidget(forms.Widget):
    """Aynı isimli (`choices`) birden çok input'u liste olarak okur.

    Template seçenek alanlarını kendisi çizer; bu widget yalnızca veriyi toplar.
    """

    def value_from_datadict(self, data, files, name):
        if hasattr(data, "getlist"):
            return data.getlist(name)
        value = data.get(name)
        return value if isinstance(value, list) else ([] if value is None else [value])


class ChoiceListField(forms.Field):
    widget = ChoiceListWidget

    def to_python(self, value):
        # Baştaki/sondaki boşlukları kırp, boş olanları at.
        return [str(item).strip() for item in (value or []) if str(item).strip()]

    def validate(self, value):
        if len(value) < MIN_CHOICES:
            raise forms.ValidationError(f"En az {MIN_CHOICES} seçenek girmelisin.")
        if len(value) > MAX_CHOICES:
            raise forms.ValidationError(f"En fazla {MAX_CHOICES} seçenek ekleyebilirsin.")
        if any(len(item) > CHOICE_MAX_LENGTH for item in value):
            raise forms.ValidationError(f"Her seçenek en fazla {CHOICE_MAX_LENGTH} karakter olabilir.")
        normalized = [item.casefold() for item in value]
        if len(set(normalized)) != len(normalized):
            raise forms.ValidationError("Aynı seçeneği iki kez yazamazsın.")


class PollForm(forms.ModelForm):
    choices = ChoiceListField(label="Seçenekler", required=False)

    class Meta:
        model = Poll
        fields = ("question", "description")
        labels = {"question": "Soru", "description": "Açıklama (isteğe bağlı)"}
        widgets = {
            "question": forms.TextInput(
                attrs={"placeholder": "Bu akşam sinemaya mı gitsem, restorana mı?", "autofocus": True}
            ),
            "description": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }
        error_messages = {
            "question": {
                "required": "Soru boş olamaz.",
                "min_length": "Soru en az 5 karakter olmalı.",
            },
        }

    def clean_question(self):
        question = self.cleaned_data["question"].strip()
        if len(question) < 5:
            raise forms.ValidationError("Soru en az 5 karakter olmalı.")
        return question

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if len(description) > 500:
            raise forms.ValidationError("Açıklama en fazla 500 karakter olabilir.")
        return description

    def choice_inputs(self):
        """Template için seçenek kutularının değerleri (en az 2, en fazla 5 kutu).

        JS kapalıyken kullanıcı 5 kutunun hepsini görür; JS açıkken
        create-poll.js boş fazlalıkları gizler ve ekle/sil butonlarını yönetir.
        """
        values = self["choices"].value() or []
        if not isinstance(values, list):
            values = [values]
        values = [str(v) for v in values][:MAX_CHOICES]
        return values + [""] * (MAX_CHOICES - len(values))
