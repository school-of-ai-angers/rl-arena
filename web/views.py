from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from core.models import Environment, User, Competitor, Revision, Tournament, TournamentParticipant, Duel
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import redirect_to_login
from web.forms import CreateAccountForm, NewRevisionForm, NewCompetitorForm
from wsgiref.util import FileWrapper
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import models
import os
import json
from importlib import import_module
from gzip import decompress

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
        'user': user,
        'competitors': user.competitor_set.order_by('environment__slug', 'name')
    })

# Main app


def home(request):
    environments = Environment.objects.order_by('name')
    return render(request, 'web/home.html', {
        'environments': environments
    })


def environment_home(request, env, tournament=None):
    environment = get_object_or_404(Environment, slug=env)

    if request.method == 'POST' and request.user.is_authenticated:
        # Handle new competitor submission
        data = request.POST.copy()
        data['environment'] = env
        form = NewCompetitorForm(data, request.FILES)
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

    if tournament is None:
        # By default, select the last finished tournament
        tournament = environment.tournament_set.filter(
            state__in=[Tournament.COMPLETED, Tournament.FAILED]).order_by('-edition').first()
        if tournament is None:
            # Fallback to first running
            tournament = environment.tournament_set.order_by(
                '-edition').first()
    else:
        tournament = get_object_or_404(
            Tournament, environment=environment, edition=tournament)

    # Prepare the list of previous and next tournaments
    if tournament is not None:
        max_edition = environment.tournament_set.aggregate(models.Max('edition'))[
            'edition__max']
        future_editions = Tournament.objects.filter(
            environment=environment,
            edition__gte=tournament.edition + 1,
            edition__lte=tournament.edition + 2
        ).order_by('edition')
        more_future_editions = tournament.edition <= max_edition - 3
        past_editions = Tournament.objects.filter(
            environment=environment,
            edition__gte=tournament.edition - 2,
            edition__lte=tournament.edition - 1
        ).order_by('edition')
        more_past_editions = tournament.edition > 3
    else:
        future_editions = []
        more_future_editions = False
        past_editions = []
        more_past_editions = False

    return render(request, 'web/environment_home.html', {
        'environment': environment,
        'active_environment_slug': env,
        'new_competitor_form': form,
        'user_competitors': user_competitors,
        'tournament': tournament,
        'past_editions': past_editions,
        'more_past_editions': more_past_editions,
        'future_editions': future_editions,
        'more_future_editions': more_future_editions,
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

    # Load revisions
    revisions = competitor.revision_set.order_by('-version_number').all()

    # Load tournaments participants
    revisions_participants = []
    for revision in revisions:
        participants = TournamentParticipant.objects.filter(
            revision=revision,
        ).order_by('-tournament__edition')
        revisions_participants.append(
            (revision, max(1, len(participants)), participants))

    return render(request, 'web/competitor_home.html', {
        'competitor': competitor,
        'active_environment_slug': env,
        'fully_visible': competitor.is_fully_visible_for(request.user),
        'revisions_participants': revisions_participants,
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


def _serve_file(file, download_name, content_type):
    """
    :param file: File
    :param content_type: str
    :returns" HttpResponse
    """
    response = HttpResponse(file.chunks(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename={download_name}'
    response['Content-Length'] = file.size
    return response


def revision_source_download(request, env, competitor, revision):
    revision = _get_fully_visible_revision(request, env, competitor, revision)
    return _serve_file(revision.zip_file, 'revision.zip', 'application/zip')


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


def duel_logs_download(request, duel_id):
    duel = get_object_or_404(Duel, id=duel_id)
    if duel.logs is None:
        raise Http404()
    return _serve_file(duel.logs, 'log.log', 'application/text')


def duel_results_download(request, duel_id):
    duel = get_object_or_404(Duel, id=duel_id)
    if duel.results is None:
        raise Http404()
    return _serve_file(duel.results, 'results.json.gz', 'application/gzip')


def tournament_participant(request, env, tournament, competitor):
    environment = get_object_or_404(Environment, slug=env)
    tournament = get_object_or_404(
        Tournament, environment=environment, edition=tournament)
    competitor = get_object_or_404(
        Competitor, environment=environment, name=competitor)
    participant = TournamentParticipant.objects.get(
        tournament=tournament, revision__competitor=competitor)
    revision = participant.revision
    duels = [
        duel.set_as_player_1(revision)
        for duel in Duel.objects.filter(tournament=tournament).filter(
            models.Q(player_1=revision) | models.Q(player_2=revision))
    ]
    duels.sort(key=lambda duel: duel.player_2.competitor.name)
    return render(request, 'web/tournament_participant.html', {
        'active_environment_slug': env,
        'environment': environment,
        'tournament': tournament,
        'competitor': competitor,
        'revision': revision,
        'participant': participant,
        'duels': duels
    })


def duel_home(request, environment, tournament, competitor_1, competitor_2, match=None):
    duel = get_object_or_404(Duel, models.Q(
        tournament__environment__slug=environment,
        tournament__edition=tournament,
        state=Duel.COMPLETED
    ) & (
        # Accept the competitors in either order
        models.Q(
            player_1__competitor__name=competitor_1,
            player_2__competitor__name=competitor_2
        ) | models.Q(
            player_1__competitor__name=competitor_2,
            player_2__competitor__name=competitor_1
        )
    ))

    # Load match
    matches = []
    with duel.results.open() as fp:
        contents = decompress(fp.read())
    matches = json.loads(contents.decode('utf-8'))['matches']

    # Prepare match links
    links_by_result = {
        'PLAYER_1_ERROR': [],
        'PLAYER_2_ERROR': [],
        'OTHER_ERROR': [],
        'PLAYER_1_WIN': [],
        'PLAYER_2_WIN': [],
        'DRAW': [],
    }
    for i, match_obj in enumerate(matches):
        links_by_result[match_obj['result']].append(
            (i, duel.get_absolute_url(i)))

    # Prepare match frames
    states_html = []
    extra_head = ''
    match_obj = None
    if match is not None:
        if match < 0 or match >= len(matches):
            return Http404()
        match_obj = matches[match]
        EnvImpl = import_module(
            f'environments.{environment}.environment').Environment
        extra_head = EnvImpl.html_head()
        players = [f'Player 1 ({duel.player_1.competitor.name})', f'Player 2 ({duel.player_2.competitor.name})']
        if match_obj['first_player'] == 'PLAYER_2':
            players = players[::-1]
        for i, state in enumerate(match_obj['states']):
            if i == 0:
                message = 'Initial state'
            else:
                message = f'{players[(i-1)%2]} moved'
            if i == len(match_obj['states']) - 1:
                message += '<br>Final state: ' + match_obj['result']
            states_html.append(
                f'<p class="text-center">{message}</p>' + EnvImpl.jsonable_to_html(state))

    return render(request, 'web/duel_home.html', {
        'active_environment_slug': environment,
        'duel': duel,
        'links_by_result': links_by_result,
        'states_html': states_html,
        'extra_head': extra_head,
        'match': match,
        'match_obj': match_obj
    })
