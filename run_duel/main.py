from yaml import safe_load
from run_duel.remote_player import RemotePlayer
from importlib import import_module
from run_duel.run_match import run_match
import json
import logging
import os
logging.basicConfig(level=os.environ['LOG_LEVEL'])
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Read args
    image_1 = os.environ['DUEL_IMAGE_1']
    image_2 = os.environ['DUEL_IMAGE_2']
    environment = os.environ['DUEL_ENVIRONMENT']
    output_file = os.environ['DUEL_OUTPUT_FILE']
    namespace = os.environ['DUEL_NAMESPACE']

    logger.info('Load environment details')
    with open(f'environments/{environment}/info.yml') as fp:
        environment_info = safe_load(fp)
    cpu_limit = environment_info['cpu_limit']
    memory_limit = environment_info['memory_limit']
    num_matches = environment_info['num_matches_in_duel']

    logger.info('Create environment')
    env = import_module(
        f'environments.{environment}.environment').Environment()

    logger.info('Boot player 1')
    player_1 = RemotePlayer(
        image_1, namespace, cpu_limit, memory_limit, 'player_1')
    logger.info('Boot player 2')
    player_2 = RemotePlayer(
        image_2, namespace, cpu_limit, memory_limit, 'player_2')

    duel_result = {
        'num_matches': 0,
        'player_1_errors': 0,
        'player_2_errors': 0,
        'other_errors': 0,
        'player_1_wins': 0,
        'player_2_wins': 0,
        'draws': 0,
        'player_1_score': 0,
        'player_2_score': 0,
        'matches': []
    }

    # Play matches (alternating who starts)
    match_num = 0

    def handle_match(player_1_starts):
        global match_num
        match = run_match(env, player_1, player_2, player_1_starts)
        if 'ERROR' in match['result']:
            logger.error(
                f'Match {match_num}: {match["result"]} with {match["error_msg"]}')
        else:
            logger.info(f'Match {match_num}: {match["result"]}')

        # Update duel
        match_num += 1
        duel_result['num_matches'] += 1
        duel_result[match['result'].lower() + 's'] += 1
        duel_result['player_1_score'] += match['player_1_score']
        duel_result['player_2_score'] += match['player_2_score']
        duel_result['matches'].append(match)

    for _ in range(0, num_matches, 2):
        handle_match(True)
        handle_match(False)

    logger.info(f'Write to {output_file}')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as fp:
        json.dump(duel_result, fp)
