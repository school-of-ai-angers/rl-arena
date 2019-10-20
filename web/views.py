from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.template import loader
from django.urls import reverse
from core.models import Environment, User, Submission
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CreateAccountForm, NewSubmissionForm

# Accounts


def create_account(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = CreateAccountForm()

    return render(request, 'web/create_account.html', {
        'form': form
    })


def user_home(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'web/user_home.html', {
        'user': user
    })

# Main app


def home(request):
    environments = Environment.objects.order_by('name')
    return render(request, 'web/home.html', {
        'environments': environments
    })


def environment_home(request, slug, new_submission_form=None):
    environment = get_object_or_404(Environment, slug=slug)
    return render(request, 'web/environment_home.html', {
        'environment': environment,
        'new_submission_form': new_submission_form or NewSubmissionForm()
    })


@login_required
def new_submission(request, slug):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    env = get_object_or_404(Environment, slug=slug)

    form = NewSubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        return environment_home(request, slug, form)

    # Prepare the object

    submission = form.save(commit=False)
    submission.submitter = request.user
    submission.environment = env
    submission.revision = Submission.objects.filter(
        submitter=request.user, environment=env).count() + 1

    # Save and return
    submission.save()
    return redirect('submission_home', slug, submission.pk)


def submission_home(request, slug, pk):
    submission = get_object_or_404(Submission, environment__slug=slug, pk=pk)
    return render(request, 'web/submission_home.html', {
        'submission': submission,
        'fully_visible': submission.is_fully_visible_for(request.user)
    })


def submission_download(request, slug, pk):
    pass


def submission_image_logs(request, slug, pk):
    pass


def submission_test_logs(request, slug, pk):
    pass
