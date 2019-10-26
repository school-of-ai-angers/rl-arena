from core.models import Environment, Tournament, Competitor, Revision, TournamentParticipant, Duel
import logging
import time
from django.db import models
logger = logging.getLogger(__name__)


def main():
    while True:
        logger.info('Start new cycle')

        # Treat each environment in order
        for env in Environment.objects.order_by('slug').all():
            logger.info(f'Check {env.slug}')
            tournament = Tournament.objects.filter(
                environment=env).order_by('-edition').first()
            if tournament is None:
                handle_new(env, set())
            elif tournament.state == 'RUNNING':
                handle_current(tournament)
            else:
                participants = set(
                    [p.zip_file for p in tournament.participants])
                handle_new(env, participants)

        time.sleep(30)


def handle_new(env, prev_competitors_set):
    logger.info(f'Handle possible new for {env.slug}')
    logger.info(
        f'Revisions that participated before were {prev_competitors_set}')

    # Gather which revisions would participate now
    passed_tests = models.Q(revision__test_state=Revision.TEST_COMPLETED)
    competitors = Competitor.objects \
        .filter(environment=env) \
        .annotate(elegible_revision=models.Max('revision__version_number', filter=passed_tests)) \
        .filter(elegible_revision__isnull=False)
    competitors_set = set((c.id, c.elegible_revision) for c in competitors)
    logger.info(f'Revisions that would participate now: {competitors_set}')

    if len(competitors_set) >= 2 and competitors_set != prev_competitors_set:
        logger.info('Will create new tournament')

        # Load revisions from db
        revisions = [
            Revision.objects.get(competitor=competitor_id,
                                 version_number=version_number)
            for competitor_id, version_number in competitors_set
        ]

        # Create new tournament
        tournament = Tournament.objects.create(
            environment=env,
            edition=Tournament.objects.filter(environment=env).count() + 1,
            state=Tournament.RUNNING
        )
        for revision in revisions:
            TournamentParticipant.objects.create(
                tournament=tournament,
                revision=revision,
                wins=0,
                losses=0,
                draws=0,
                points=0,
                total_score=0,
                ranking=1
            )

        # Create new duels
        # This section is based on:
        # https://en.wikipedia.org/wiki/Round-robin_tournament#Scheduling_algorithm
        if len(revisions) % 2 == 1:
            # Ensure the number of players is even
            # Matching against the None player means having a bye
            revisions.append(None)
        for round_n in range(len(revisions)-1):
            # Match players (a, N-a)
            for i in range(len(revisions)//2):
                j = len(revisions) - i - 1
                revision_1, revision_2 = revisions[i], revisions[j]
                if revision_1 is None or revision_2 is None:
                    continue
                duel = Duel.objects.create(
                    tournament=tournament,
                    player_1=revision_1,
                    player_2=revision_2,
                )

            # Rotate players (keeping the first fixed)
            # 0, 1, 2, 3, 4 -> 0, 4, 1, 2, 3
            revisions[1:] = [revisions[-1], *revisions[1:-1]]

        logger.info(
            f'Tournament {tournament} created with {len(revisions)} players')


def handle_current(tournament):
    pass
