from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from core.models import Environment, User, Competitor, Revision
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import redirect_to_login
from .forms import CreateAccountForm, NewRevisionForm, NewCompetitorForm
from wsgiref.util import FileWrapper
from django.core.exceptions import PermissionDenied
from django.contrib import messages
import os

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


@login_required
def profile(request):
    return redirect('user_home', request.user.username)


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


def environment_home(request, env):
    environment = get_object_or_404(Environment, slug=env)

    if request.method == 'POST' and request.user.is_authenticated:
        # Handle new competitor submission
        form = NewCompetitorForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(
                request, 'Failed to submit form, please check error messages')
        else:
            # Prepare the new objects
            form_data = form.cleaned_data
            competitor = Competitor.objects.create(
                submitter=request.user,
                environment=environment,
                is_public=form_data['is_public'],
                name=form_data['name'],
                last_version=1
            )
            revision = Revision.objects.create(
                competitor=competitor,
                version_number=1,
                zip_file=form_data['zip_file'],
                publish_state=Revision.PUBLISH_SCHEDULED if form_data[
                    'is_public'] else Revision.PUBLISH_SKIPPED
            )
            return redirect('competitor_home', environment.slug, competitor.name)
    else:
        form = NewCompetitorForm()

    # List user competitors
    if request.user.is_authenticated:
        user_competitors = environment.competitor_set.filter(
            submitter=request.user).order_by('name').all()
    else:
        user_competitors = []

    return render(request, 'web/environment_home.html', {
        'environment': environment,
        'active_environment_slug': env,
        'new_competitor_form': form,
        'user_competitors': user_competitors
    })


def competitor_home(request, env, competitor):
    competitor = get_object_or_404(
        Competitor, environment__slug=env, name=competitor)

    if request.method == 'POST' and request.user.is_authenticated and competitor.submitter == request.user:
        # Handle new revision submission
        form = NewRevisionForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(
                request, 'Failed to submit form, please check error messages')
        else:
            # Prepare the new object
            form_data = form.cleaned_data
            competitor.last_version += 1
            competitor.save()
            revision = Revision.objects.create(
                competitor=competitor,
                version_number=competitor.last_version,
                zip_file=form_data['zip_file'],
                publish_state=Revision.PUBLISH_SCHEDULED if competitor.is_public else Revision.PUBLISH_SKIPPED
            )
    else:
        form = NewRevisionForm()

    return render(request, 'web/competitor_home.html', {
        'competitor': competitor,
        'active_environment_slug': env,
        'fully_visible': competitor.is_fully_visible_for(request.user),
        'revisions': competitor.revision_set.order_by('version_number').all(),
        'new_revision_form': form
    })


def _get_fully_visible_revision(request, env, competitor, revision):
    """
    :param request:
    :param env: str
    :param competitor: str
    :param revision: int
    :returns: Revision
    """
    competitor = get_object_or_404(
        Competitor, environment__slug=env, name=competitor)
    if not competitor.is_fully_visible_for(request.user):
        raise PermissionDenied()
    return get_object_or_404(Revision, competitor=competitor, version_number=revision)


def _serve_file(file_path, download_name, content_type):
    """
    :param file_path: str
    :param content_type: str
    :returns" HttpResponse
    """
    wrapper = FileWrapper(open(file_path, 'rb'))
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename={download_name}'
    response['Content-Length'] = os.path.getsize(file_path)
    return response


def revision_source_download(request, env, competitor, revision):
    revision = _get_fully_visible_revision(request, env, competitor, revision)
    return _serve_file(revision.zip_file.path, 'revision.zip', 'application/zip')


def revision_image_logs_download(request, env, competitor, revision):
    revision = _get_fully_visible_revision(request, env, competitor, revision)
    if revision.image_logs is None:
        raise Http404()
    return _serve_file(revision.image_logs, 'image.log', 'application/text')


def revision_test_logs_download(request, env, competitor, revision):
    revision = _get_fully_visible_revision(request, env, competitor, revision)
    if revision.test_logs is None:
        raise Http404()
    return _serve_file(revision.test_logs, 'test.log', 'application/text')
