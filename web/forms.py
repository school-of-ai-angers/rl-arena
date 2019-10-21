from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User, Submission
from django.core.exceptions import ValidationError
import os

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


class NewSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('zip_file', 'github_source', 'is_public')
