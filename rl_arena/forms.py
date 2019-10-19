from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CreateAccountForm(UserCreationForm):
    github = forms.CharField(
        max_length=100, required=False, help_text='Your GitHub user (optional)')

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'username', 'github')
