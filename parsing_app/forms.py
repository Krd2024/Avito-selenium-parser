from django import forms
from .models import RequestUser


class RequestUserForm(forms.ModelForm):
    url = forms.URLField(
        required=False,
        label="URL с фильтрами",
        help_text=(
            "Вставьте полную ссылку на Avito с нужными фильтрами "
            "(категория, цена и т.д.). Если указано — фраза и город "
            "используются только для идентификации запроса."
        ),
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://www.avito.ru/moskva/telefony/...?q=телефон&f=...",
                "class": "form-field-input",
            }
        ),
    )
    price_from = forms.IntegerField(
        required=False,
        label="Цена от",
        widget=forms.NumberInput(
            attrs={"placeholder": "например, 1000", "class": "form-field-input"}
        ),
    )
    price_to = forms.IntegerField(
        required=False,
        label="Цена до",
        widget=forms.NumberInput(
            attrs={"placeholder": "например, 30000", "class": "form-field-input"}
        ),
    )

    class Meta:
        model = RequestUser
        fields = ["search_phrase", "sity", "url", "price_from", "price_to"]

    def clean(self):
        cleaned = super().clean()
        pf = cleaned.get("price_from")
        pt = cleaned.get("price_to")
        if pf is not None and pt is not None and pf > pt:
            raise forms.ValidationError("«Цена от» не может быть больше «цены до».")
        return cleaned
