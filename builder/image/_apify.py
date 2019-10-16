# This file will expose the player as a HTTP API

from flask import Flask, escape, request
from sample_player.player import Player
import numpy as np

app = Flask(__name__)
player = Player(False)


@app.route('/start', methods=['POST'])
def start():
    data = request.json
    state = np.asarray(data['state'])
    valid_actions = np.asarray(data['valid_actions'])
    action = player.start(state, valid_actions)
    return {
        'action': int(action)
    }


@app.route('/step', methods=['POST'])
def step():
    data = request.json
    state = np.asarray(data['state'])
    valid_actions = np.asarray(data['valid_actions'])
    prev_reward = data['prev_reward']
    action = player.step(state, valid_actions, prev_reward)
    return {
        'action': int(action)
    }


@app.route('/end', methods=['POST'])
def end():
    data = request.json
    state = np.asarray(data['state'])
    prev_reward = data['prev_reward']
    player.end(state, prev_reward)
    return {}
