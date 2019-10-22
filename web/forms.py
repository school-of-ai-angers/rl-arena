from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User, Revision
from django.core.exceptions import ValidationError
import os
from django.core.validators import FileExtensionValidator

expected_invitation_code = os.environ['INVITATION_CODE']


def validate_invitation_code(value):
    if value != expected_invitation_code:
        raise ValidationError('Incorrect invitation code')


class CreateAccountForm(UserCreationForm):

    invitation_code = forms.CharField(
        label='Invitation code', max_length=100,
        required=True, help_text='For security reasons, only invited people can create their account. Please request your invitation code to an organizer', validators=[validate_invitation_code])

    class Meta:
        model = User
        fields = ('invitation_code', 'email', 'password1',
                  'password2', 'username', 'github')


class NewCompetitorForm(forms.Form):
    name = forms.SlugField(help_text='A nice nickname for your competitor')
    zip_file = forms.FileField(
        label='Source code (as a .zip file)', validators=[
            FileExtensionValidator(['zip'])])
    is_public = forms.BooleanField(
        label='Make public', help_text='I want to share my source code openly with the community', required=False)


class NewRevisionForm(forms.ModelForm):
    class Meta:
        model = Revision
        fields = ('zip_file',)
