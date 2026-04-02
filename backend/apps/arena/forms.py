from django import forms
from .models import CredentialsArena


class CredentialsArenaForm(forms.ModelForm):
    class Meta:
        model = CredentialsArena
        fields = ["nome_maquina", "client_id", "client_secret", "api_key"]
        widgets = {
            "nome_maquina": forms.TextInput(attrs={"class": "form-control"}),
            "client_id": forms.TextInput(attrs={"class": "form-control"}),
            "client_secret": forms.TextInput(attrs={"class": "form-control"}),
            "api_key": forms.TextInput(attrs={"class": "form-control"}),
        }
