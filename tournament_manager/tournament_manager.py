from core.models import Environment, Tournament, Competitor, Revision, TournamentParticipant, Duel
import logging
import time
from django.db import models
from django.utils import timezone
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
                    (revision.competitor.id, revision.version_number)
                    for revision in tournament.participants.all()
                )
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
        total_duels = len(competitors_set) * (len(competitors_set) - 1) / 2
        tournament = Tournament.objects.create(
            environment=env,
            edition=Tournament.objects.filter(environment=env).count() + 1,
            state=Tournament.RUNNING,
            total_duels=total_duels
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
    # Load participants
    participants = TournamentParticipant.objects.filter(
        tournament=tournament).all()
    logger.info(f'Loaded {len(participants)} participants')

    # Reset counters
    tournament.total_duels = 0
    tournament.completed_duels = 0
    tournament.failed_duels = 0
    participant_by_revision = {}
    for p in participants:
        p.wins = 0
        p.losses = 0
        p.draws = 0
        p.total_score = 0
        participant_by_revision[p.revision] = p

    # Update counters
    def add_win(winner, winner_score, loser, loser_score):
        winner = participant_by_revision[winner]
        loser = participant_by_revision[loser]
        winner.wins += 1
        loser.losses += 1
        winner.total_score += winner_score
        loser.total_score += loser_score

    def add_draw(player, score):
        player = participant_by_revision[player]
        player.draws += 1
        player.total_score += score

    for duel in tournament.duel_set.all():
        tournament.total_duels += 1
        if duel.state == Duel.COMPLETED:
            tournament.completed_duels += 1
            if duel.result == Duel.PLAYER_1_WIN:
                add_win(duel.player_1, duel.player_1_score,
                        duel.player_2, duel.player_2_score)
            elif duel.result == Duel.PLAYER_2_WIN:
                add_win(duel.player_2, duel.player_2_score,
                        duel.player_1, duel.player_1_score)
            else:
                add_draw(duel.player_1)
                add_draw(duel.player_2)
        elif duel.state == Duel.FAILED:
            tournament.failed_duels += 1
            add_draw(duel.player_1, duel.player_1_score or 0.)
            add_draw(duel.player_2, duel.player_2_score or 0.)

    # Update ranking
    # Build a list of tuples: (participant, ranking_values)
    ranking_builder = []
    for p in participants:
        p.points = 2 * p.wins + p.draws
        ranking_builder.append((p, (p.points, p.wins, p.total_score)))

    # Sort and calculate ranking
    ranking_builder.sort(key=lambda x: x[1], reverse=True)
    logger.info(f'Ranking values are: {[x[1] for x in ranking_builder]}')
    prev_values = None
    prev_ranking = -1
    for ranking, (p, values) in enumerate(ranking_builder, start=1):
        if values != prev_values:
            p.ranking = ranking
            prev_values = values
            prev_ranking = ranking
        else:
            # Tied
            p.ranking = prev_ranking

    # End of tournament
    if tournament.failed_duels + tournament.completed_duels == tournament.total_duels:
        tournament.ended_at = timezone.now()
        tournament.state = Tournament.COMPLETED if tournament.failed_duels == 0 else Tournament.FAILED
    logger.info(
        f'failed_duels={tournament.failed_duels}, completed_duels={tournament.completed_duels}, total_duels={tournament.total_duels}')

    # Save
    tournament.save()
    for p in participants:
        p.save()
