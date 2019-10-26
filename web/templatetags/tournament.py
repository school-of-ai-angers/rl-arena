from django import template
from core.models import TournamentParticipant, Duel
from django.db import models

register = template.Library()


@register.inclusion_tag('web/tournament.html')
def tournament(tournament):
    """
    Draws the tournament table
    """
    players = TournamentParticipant.objects.filter(
        tournament=tournament
    ).order_by('ranking', 'revision__competitor__name').all()

    total_duels = Duel.objects.filter(tournament=tournament).count()
    finished_duels = Duel.objects.filter(tournament=tournament, state__in=[
                                         Duel.FAILED, Duel.COMPLETED]).count()

    prev_ranking = None
    rankings = []
    for player in players:
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
        'finished_duels': finished_duels,
        'total_duels': total_duels,
        'progress_width': 100 * finished_duels / total_duels,
        'players_and_rankings': list(zip(players, rankings))
    }
