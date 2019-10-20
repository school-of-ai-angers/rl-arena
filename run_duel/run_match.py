import traceback


def run_match(env, player_1, player_2, player_1_starts):
    """
    :param env: Environment
    :param player_1, player_2: Player
    :param player_1_starts: bool
    :returns: dict
    """
    states = []
    success = False
    result = {
        'result': '',
        'error_msg': '',
        'player_1_score': 0,
        'player_2_score': 0,
        'first_player': 'PLAYER_1' if player_1_starts else 'PLAYER_2',
        'states': states,
    }

    # Translate (1,2) -> (A,B)
    if player_1_starts:
        player_a, player_b = player_1, player_2
    else:
        player_a, player_b = player_2, player_1
    score_a = 0

    # Keep track of the culprit in case of error
    guilty = 'X'
    guilty_map = {
        'X': 'OTHER_ERROR',
        'A': 'PLAYER_1_ERROR' if player_1_starts else 'PLAYER_2_ERROR',
        'B': 'PLAYER_2_ERROR' if player_1_starts else 'PLAYER_1_ERROR'
    }
    try:
        # Reset board
        state, valid_actions = env.reset()
        states.append(env.to_jsonable())

        # First moves
        guilty = 'A'
        action = player_a.start(state, valid_actions)
        state, reward_a, done, valid_actions = env.step(action)
        guilty = 'X'
        states.append(env.to_jsonable())
        score_a += reward_a
        assert not done
        guilty = 'B'
        action = player_b.start(state, valid_actions)
        state, reward_b, done, valid_actions = env.step(action)
        guilty = 'X'
        states.append(env.to_jsonable())
        score_a -= reward_b
        assert not done

        # Loop for the rest of the game
        while True:
            # A
            guilty = 'A'
            action = player_a.step(state, valid_actions, reward_a - reward_b)
            state, reward_a, done, valid_actions = env.step(action)
            guilty = 'X'
            states.append(env.to_jsonable())
            score_a += reward_a
            if done:
                guilty = 'A'
                player_a.end(state, reward_a)
                guilty = 'B'
                player_b.end(state, reward_b - reward_a)
                guilty = 'X'
                break

            # B
            guilty = 'B'
            action = player_b.step(state, valid_actions, reward_b - reward_a)
            state, reward_b, done, valid_actions = env.step(action)
            guilty = 'X'
            states.append(env.to_jsonable())
            score_a -= reward_b
            if done:
                guilty = 'A'
                player_a.end(state, reward_a - reward_b)
                guilty = 'B'
                player_b.end(state, reward_b)
                guilty = 'X'
                break

        success = True
    except:
        # Match failed
        result['result'] = guilty_map[guilty]
        result['error_msg'] = traceback.format_exc()

    # Translate back (A,B) -> (1,2)
    if player_1_starts:
        score_1, score_2 = score_a, -score_a
    else:
        score_1, score_2 = -score_a, score_a

    result['player_1_score'] = score_1
    result['player_2_score'] = score_2
    if success:
        result['result'] = 'DRAW' if score_1 == score_2 \
            else 'PLAYER_1_WIN' if score_1 > score_2 \
            else 'PLAYER_2_WIN'

    return result
