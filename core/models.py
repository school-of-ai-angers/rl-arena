from django.db import models
from core.settings import MEDIA_ROOT
from django.core.validators import RegexValidator, FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from markdown import markdown
import uuid


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
    memory_limit = models.CharField(max_length=50)
    cpu_limit = models.FloatField()
    # The name of the image in the static folder
    image = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def description_html(self):
        """ Return the description in HTML text """
        return markdown(self.description)

    @property
    def num_competitors(self):
        """ The number of competitors """
        return self.competitor_set.count()

    @property
    def num_submitters(self):
        """ The number of users that submitted their players """
        return self.competitor_set.values('submitter').distinct().count()

    @property
    def image_static(self):
        """ The static image file name """
        return f'environment-{self.slug}/{self.image}'


class User(AbstractUser):
    """ A submitter """
    email = models.EmailField(
        unique=True, help_text='Your email address will not be made public and will not be used for communications. It will only be used as your authentication identifier.')
    # GitHub account
    github = models.CharField(
        max_length=100, blank=True,
        validators=[UnicodeUsernameValidator],
        help_text='Your GitHub username if you have one and want to link to it')

    # User email for login, since it is much easier to remember
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Competitor(models.Model):
    """ Represents a linear of players submitted by an user """
    # The user who sent this entry
    submitter = models.ForeignKey(User, models.CASCADE)
    # The target environment
    environment = models.ForeignKey(Environment, models.CASCADE)
    # Whether the source is public
    is_public = models.BooleanField()
    # The display and URL name
    name = models.SlugField()
    # The number of the last version
    last_version = models.PositiveIntegerField()

    def is_fully_visible_for(self, user):
        """ Determines whether all information about this submission is accessible by the given user """
        return self.is_public or user.is_superuser or self.submitter == user

    @property
    def last_revision(self):
        """ Link to the revion with the last version """
        return Revision.objects.get(competitor=self, version_number=self.last_version)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['environment', 'name'], name='unique_environment')
        ]


def zip_file_path(instance, filename):
    return f'revisions/{uuid.uuid4()}.zip'


class Revision(models.Model):
    """ Represents each submitted code, as part of a competitor lineage """
    # The competitor family (PROTECT because this entity has external persistent state)
    competitor = models.ForeignKey(Competitor, models.PROTECT)
    # The submission counter for this competitor (starts at 1)
    version_number = models.PositiveIntegerField()
    # The date of submission
    created_at = models.DateTimeField(auto_now_add=True)
    # The ZIPped source
    zip_file = models.FileField(
        upload_to=zip_file_path, validators=[FileExtensionValidator(['zip'])])

    # Source publishing state
    PUBLISH_SCHEDULED = 'PUBLISH_SCHEDULED'
    PUBLISH_RUNNING = 'PUBLISH_RUNNING'
    PUBLISH_FAILED = 'PUBLISH_FAILED'
    PUBLISH_COMPLETED = 'PUBLISH_COMPLETED'
    # Will not publish a private competitor
    PUBLISH_SKIPPED = 'PUBLISH_SKIPPED'
    publish_state = models.CharField(max_length=100, choices=_choices_with([
        PUBLISH_SKIPPED,
        PUBLISH_SCHEDULED,
        PUBLISH_RUNNING,
        PUBLISH_FAILED,
        PUBLISH_COMPLETED]))

    # When the publish process started and ended
    publish_started_at = models.DateTimeField(null=True)
    publish_ended_at = models.DateTimeField(null=True)
    # Main reason for the failed publish
    publish_error_msg = models.CharField(blank=True, max_length=200)
    # Link to GitHub sources (only present for public source code)
    publish_url = models.CharField(max_length=200, blank=True, validators=[RegexValidator(
        r'^https://github.com/')])

    # Docker image building state
    IMAGE_SCHEDULED = 'IMAGE_SCHEDULED'
    IMAGE_RUNNING = 'IMAGE_RUNNING'
    IMAGE_FAILED = 'IMAGE_FAILED'
    IMAGE_COMPLETED = 'IMAGE_COMPLETED'
    image_state = models.CharField(max_length=100, choices=_choices_with([
        IMAGE_SCHEDULED,
        IMAGE_RUNNING,
        IMAGE_FAILED,
        IMAGE_COMPLETED]), default=IMAGE_SCHEDULED)

    # When the build process started and ended
    image_started_at = models.DateTimeField(null=True)
    image_ended_at = models.DateTimeField(null=True)
    # Main reason for the failed build
    image_error_msg = models.CharField(blank=True, max_length=200)
    # Docker image name and tag
    image_name = models.CharField(blank=True, max_length=200)
    # Docker build logs
    image_logs = models.FilePathField(
        null=True, path=MEDIA_ROOT+'revision_image_logs/')

    # Smoke testing state
    TEST_SCHEDULED = 'TEST_SCHEDULED'
    TEST_RUNNING = 'TEST_RUNNING'
    TEST_FAILED = 'TEST_FAILED'
    TEST_COMPLETED = 'TEST_COMPLETED'
    test_state = models.CharField(max_length=100, choices=_choices_with([
        TEST_SCHEDULED,
        TEST_RUNNING,
        TEST_FAILED,
        TEST_COMPLETED]), default=TEST_SCHEDULED)

    # When the smoke test process started and ended
    test_started_at = models.DateTimeField(null=True)
    test_ended_at = models.DateTimeField(null=True)
    # Main reason for the failed smoke test
    test_error_msg = models.CharField(blank=True, max_length=200)
    # Smoke test logs
    test_logs = models.FilePathField(
        null=True, path=MEDIA_ROOT+'revision_test_logs/')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['competitor', 'version_number'], name='unique_competitor')
        ]


class TournamentParticipant(models.Model):
    """ Represent a participation on a tournament """
    tournament = models.ForeignKey('Tournament', models.CASCADE)
    revision = models.ForeignKey(Revision, models.CASCADE)
    # Number of duels that were won, lost or tied
    wins = models.PositiveIntegerField()
    losses = models.PositiveIntegerField()
    draws = models.PositiveIntegerField()
    # points = 2 * wins + draws
    points = models.PositiveIntegerField()
    # The sum of all duels' scores
    total_score = models.FloatField()
    # The ranking of this submission, starting from 1.
    # Revisions are ranked by (points, wins, total_score)
    # In the case of a drawn, tied submissions will have the same ranking, skipping
    # the next ones. For example, if first place is tied: 1, 1, 3
    ranking = models.PositiveIntegerField()


class Tournament(models.Model):
    """
    Represent tournaments composed of multiples matches between
    ready revisions for a given environment
    """
    # The scope of the competition
    environment = models.ForeignKey(Environment, models.CASCADE)
    # Who participates and their performance
    participants = models.ManyToManyField(
        Revision, through=TournamentParticipant)
    # A sequential counter for the number of tournaments for this environment (starting at 1)
    edition = models.PositiveIntegerField()
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


class Duel(models.Model):
    """ Represent multiple matches between two players of the same tournament """
    tournament = models.ForeignKey(Tournament, models.CASCADE)

    # The two participating players
    player_1 = models.ForeignKey(
        Revision, models.CASCADE, related_name='player_1')
    player_2 = models.ForeignKey(
        Revision, models.CASCADE, related_name='player_2')

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

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    logs = models.FilePathField(null=True, path=MEDIA_ROOT+'duel_logs/')
    results = models.FilePathField(null=True, path=MEDIA_ROOT+'duel_results/')

    # Duel results
    ERROR = 'ERROR'
    PLAYER_1_WIN = 'PLAYER_1_WIN'
    PLAYER_2_WIN = 'PLAYER_2_WIN'
    DRAW = 'DRAW'
    result = models.CharField(max_length=100, choices=_choices_with([
        ERROR,
        PLAYER_1_WIN,
        PLAYER_2_WIN,
        DRAW]), blank=True)
    error_msg = models.CharField(max_length=200, blank=True)
    num_matches = models.PositiveIntegerField(null=True)
    player_1_errors = models.PositiveIntegerField(null=True)
    player_2_errors = models.PositiveIntegerField(null=True)
    other_errors = models.PositiveIntegerField(null=True)
    player_1_wins = models.PositiveIntegerField(null=True)
    player_2_wins = models.PositiveIntegerField(null=True)
    draws = models.PositiveIntegerField(null=True)
    player_1_score = models.FloatField(null=True)
    player_2_score = models.FloatField(null=True)
