from django.db import models
from rl_arena.settings import MEDIA_ROOT
from django.core.validators import RegexValidator, FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from markdown import markdown


def _choices_with(values):
    return [(value, '') for value in values]


class Environment(models.Model):
    """ Describe a game environment, like TicTacToe, Chess, etc """
    # Display name
    name = models.CharField(max_length=100)
    # URL name
    slug = models.SlugField(unique=True)
    # Markdown description
    description = models.TextField()
    # How many matches will be played in each duel. Should be an even number,
    # because players will alternate who starts
    num_matches_in_duel = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def description_html(self):
        """ Return the description in HTML text """
        return markdown(self.description)


class User(AbstractUser):
    """ A submitter """
    email = models.EmailField(
        unique=True, help_text='Will not made public in any way and will not be used for communications')
    # GitHub account
    github = models.CharField(max_length=100, blank=True)

    # User email for login, since it is much easier to remember
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Submission(models.Model):
    """ Represents each submitted code """
    # The user who sent this entry (PROTECT because this entity has external persistent state)
    submitter = models.ForeignKey(User, models.PROTECT)
    # The target environment
    environment = models.ForeignKey(Environment, models.PROTECT)
    # How many submissions where made before this one by this user for this
    # environment (starts at 1)
    revision = models.PositiveIntegerField()
    # The date of submission
    created_at = models.DateTimeField(auto_now_add=True)
    # The ZIPped source
    zip_file = models.FileField(
        upload_to='submissions/', validators=[FileExtensionValidator(['zip'])])
    # Link to GitHub sources
    github_source = models.CharField(max_length=200, blank=True, validators=[RegexValidator(
        r'^https://github.com/[^/]+/[^/]+/tree/[^/]+$')])
    # Whether the source is public
    is_public = models.BooleanField()

    # Current state
    # Code was submitted. Waiting to build
    WAITING_BUILD = 'WAITING_BUILD'
    # Image build is running
    BUILDING = 'BUILDING'
    # Failed to build a Docker image for it
    BUILD_FAILED = 'BUILD_FAILED'
    # Image was built. Waiting for smoke test
    WAITING_SMOKE_TEST = 'WAITING_SMOKE_TEST'
    # Smoke testing is running
    TESTING = 'TESTING'
    # Smoke test failed
    FAILED_SMOKE_TEST = 'FAILED_SMOKE_TEST'
    # Everything seems ready
    READY = 'READY'
    state = models.CharField(max_length=100, choices=_choices_with([
        WAITING_BUILD,
        BUILDING,
        BUILD_FAILED,
        WAITING_SMOKE_TEST,
        TESTING,
        FAILED_SMOKE_TEST,
        READY,
    ]), default=WAITING_BUILD)

    # Docker image data

    # When the build process started and ended
    image_started_at = models.DateTimeField(null=True)
    image_ended_at = models.DateTimeField(null=True)
    # Docker image name and tag
    image_name = models.CharField(blank=True, max_length=200)
    # Docker build logs
    image_logs = models.FilePathField(
        null=True, path=MEDIA_ROOT+'submission_image_logs/')

    # Smoke test data

    # When the smoke test process started and ended
    test_started_at = models.DateTimeField(null=True)
    test_ended_at = models.DateTimeField(null=True)
    # Smoke test logs
    test_logs = models.FilePathField(
        null=True, path=MEDIA_ROOT+'submission_test_logs/')

    def is_fully_visible_for(self, user):
        """ Determines whether all information about this submission is accessible by the given user """
        return self.is_public or user.is_superuser or self.submitter == user


class TournamentSubmission(models.Model):
    """ Represent a submission participation on a tournament """
    tournament = models.ForeignKey('Tournament', models.CASCADE)
    submission = models.ForeignKey('Submission', models.CASCADE)
    # Number of duels that were won, lost or tied
    wins = models.PositiveIntegerField()
    losses = models.PositiveIntegerField()
    draws = models.PositiveIntegerField()
    # points = 2 * wins + draws
    points = models.PositiveIntegerField()
    # The sum of all duels' scores
    total_score = models.FloatField()
    # The ranking of this submission, starting from 1.
    # Submissions are ranked by (points, wins, total_score)
    # In the case of a drawn, tied submissions will have the same ranking, skipping
    # the next ones. For example, if first place is tied: 1, 1, 3
    ranking = models.PositiveIntegerField()


class Tournament(models.Model):
    """
    Represent tournaments composed of multiples matches between
    ready submissions for a given environment
    """
    environment = models.ForeignKey(Environment, models.CASCADE)
    # A sequential counter for the number of tournaments for this environment
    # (starting at 1)
    edition = models.PositiveIntegerField()
    # The duels inside a tournament are played in rounds, so that during the tournament
    # the number of duels played per submission increases in lock-step. (starts at 1)
    current_round = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)

    # States
    RUNNING = 'RUNNING'
    FAILED = 'FAILED'
    COMPLETED = 'COMPLETED'
    state = models.CharField(max_length=100, choices=_choices_with([
        RUNNING,
        FAILED,
        COMPLETED]), default=RUNNING)

    ended_at = models.DateTimeField(null=True)
    submissions = models.ManyToManyField(
        Submission, through=TournamentSubmission)


class DuelSubmission(models.Model):
    """ Represent a submission participation on a duel """
    duel = models.ForeignKey('Duel', models.CASCADE)
    submission = models.ForeignKey('Submission', models.CASCADE)
    # The submission performace one-hot encoded, that is, after the duel is finished
    # exactly one of win, loss, draw will be 1
    win = models.PositiveIntegerField()
    loss = models.PositiveIntegerField()
    draw = models.PositiveIntegerField()
    # Sum of the score of all matches of this submissions
    score = models.FloatField()


class Duel(models.Model):
    """ Represent multiple matches between two submissions. """
    tournament = models.ForeignKey(Tournament, models.CASCADE)
    # See definition of `round` in Tournament
    round = models.PositiveIntegerField()
    # How many matches will be played in this duel
    num_matches = models.PositiveIntegerField()
    # The two participating submissions and their performance
    submissions = models.ManyToManyField(Submission, through=DuelSubmission)

    # States
    SCHEDULED = 'SCHEDULED'
    RUNNING = 'RUNNING'
    FAILED = 'FAILED'
    COMPLETED = 'COMPLETED'
    state = models.CharField(max_length=100, choices=_choices_with([
        SCHEDULED,
        RUNNING,
        FAILED,
        COMPLETED]), default=SCHEDULED)

    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    logs = models.FilePathField(null=True, path=MEDIA_ROOT+'duel_logs/')
