from yaml import safe_load
import os
from run_duel.remote_player import RemotePlayer
from importlib import import_module
from run_duel.run_match import run_match
import json

if __name__ == "__main__":
    # Read args
    image_1 = os.environ['DUEL_IMAGE_1']
    image_2 = os.environ['DUEL_IMAGE_2']
    environment = os.environ['DUEL_ENVIRONMENT']
    output_file = os.environ['DUEL_OUTPUT_FILE']
    namespace = os.environ['DUEL_NAMESPACE']

    print('=== Load environment details ===')
    with open(f'environments/{environment}/info.yml') as fp:
        environment_info = safe_load(fp)
    cpu_limit = environment_info['cpu_limit']
    memory_limit = environment_info['memory_limit']
    num_matches = environment_info['num_matches_in_duel']

    print('=== Create environment ===')
    env = import_module(
        f'environments.{environment}.environment').Environment()

    print('=== Boot player 1 ===')
    player_1 = RemotePlayer(
        image_1, namespace, cpu_limit, memory_limit, 'player_1')
    print('=== Boot player 2 ===')
    player_2 = RemotePlayer(
        image_2, namespace, cpu_limit, memory_limit, 'player_2')

    result = {
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
    def handle_match(player_1_starts):
        match = run_match(env, player_1, player_2, player_1_starts)
        result['num_matches'] += 1
        result[match['result'].lower() + 's'] += 1
        result['player_1_score'] += match['player_1_score']
        result['player_2_score'] += match['player_2_score']
        result['matches'].append(match)
    for i in range(0, num_matches, 2):
        print(f'Play match {i}')
        handle_match(True)
        handle_match(False)

    print('=== Write to file ===')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as fp:
        json.dump(result, fp)
