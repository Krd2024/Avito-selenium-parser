from django import forms
from .models import RequestUser


class RequestUserForm(forms.ModelForm):
    class Meta:
        model = RequestUser
        fields = ["search_phrase", "sity"]


# class ResultsUserRequestForm(forms.ModelForm):
#     class Meta:
#         model = ResultParsing
#         fields =
