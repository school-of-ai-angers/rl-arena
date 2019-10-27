from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User, Revision, Competitor
from django.core.exceptions import ValidationError
import os
from django.core.validators import FileExtensionValidator

expected_invitation_code = os.environ['INVITATION_CODE']
teams = os.environ['TEAMS'].split(',')


def validate_invitation_code(value):
    if value != expected_invitation_code:
        raise ValidationError('Incorrect invitation code')


class CreateAccountForm(UserCreationForm):

    invitation_code = forms.CharField(
        label='Invitation code', max_length=100,
        required=True, help_text='For security reasons, only invited people can create their account. Please request your invitation code to an organizer', validators=[validate_invitation_code])
    team = forms.ChoiceField(label='Select your team', required=True, choices=[
        (None, '--- Select one ---'),
        *[(t, t) for t in teams]
    ])

    class Meta:
        model = User
        fields = ('invitation_code', 'team', 'email', 'password1',
                  'password2', 'username', 'github')


class NewCompetitorForm(forms.Form):
    environment = forms.CharField(widget=forms.HiddenInput())
    name = forms.SlugField(help_text='A nice nickname for your competitor')
    zip_file = forms.FileField(
        label='Source code (as a .zip file)', validators=[
            FileExtensionValidator(['zip'])])
    is_public = forms.BooleanField(
        label='Make public', help_text='I want to share my source code openly with the community', required=False)

    def clean(self):
        # Load data
        super().clean()
        environment = self.cleaned_data.get('environment')
        name = self.cleaned_data.get('name')
        if environment is not None and name is not None:
            # Check unicity
            exists = Competitor.objects.filter(
                environment__slug=environment, name=name).exists()
            if exists:
                self.add_error(
                    'name', 'Another competitor with this name already exists. Please try a different one')


class NewRevisionForm(forms.Form):
    zip_file = forms.FileField(
        label='Source code (as a .zip file)', validators=[
            FileExtensionValidator(['zip'])])
