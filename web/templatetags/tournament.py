from django import template
from core.models import TournamentParticipant, Duel
from django.db import models

register = template.Library()


@register.inclusion_tag('web/tournament.html')
def tournament(tournament):
    """
    Draws the tournament table
    """
    participants = TournamentParticipant.objects.filter(
        tournament=tournament
    ).order_by('ranking', 'revision__competitor__name').all()

    prev_ranking = None
    rankings = []
    for player in participants:
        if prev_ranking is None or player.ranking != prev_ranking['ranking']:
            prev_ranking = {
                'ranking': player.ranking,
                'span': 1
            }
            rankings.append(prev_ranking)
        else:
            prev_ranking['span'] += 1
            rankings.append(None)

    return {
        'tournament': tournament,
        'good_progress_width': 100 * tournament.completed_duels / tournament.total_duels,
        'bad_progress_width': 100 * tournament.failed_duels / tournament.total_duels,
        'participants_and_rankings': list(zip(participants, rankings))
    }
