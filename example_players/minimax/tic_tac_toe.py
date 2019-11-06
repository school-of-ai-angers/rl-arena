import numpy as np


class Environment:
    def __init__(self):
        # Encode the board as 9 positions with 0 (empty), 1 (first player) or -1 (second player).
        # The position at line `i` and column `j` will be at `3*i+j`.
        # The 10-th position is the current player (-1 or 1)
        self.state = np.zeros((10,))
        # Win lines
        self.lines = [
            # Horizontal
            *[[n, n + 1, n + 2] for n in [0, 3, 6]],
            # Vertical
            *[[n, n + 3, n + 6] for n in [0, 1, 2]],
            # Diagonal
            [0, 4, 8], [2, 4, 6]
        ]

    def reset(self):
        """
        Reset the game, returning:
        - the new state
        - the list of valid actions
        """
        self.state[:9] = 0
        self.state[9] = 1
        return self.state, np.arange(9)

    def step(self, action):
        """
        Apply the given action, returning:
        - the new state
        - the immediate reward of this action
        - a flag telling whether the game has finished
        - the list of valid actions
        """
        # Play
        assert self.state[action] == 0, 'Invalid action'
        self.state[action] = self.state[9]

        # Check end of game
        for line in self.lines:
            marks = self.state[line]
            if marks[0] != 0 and marks[0] == marks[1] and marks[1] == marks[2]:
                # Current player won
                return self.state, 1, True, []
        if np.all(self.state != 0):
            # Tie
            return self.state, 0, True, []

        # Prepare next play
        self.state[9] = -self.state[9]
        return self.state, 0, False, np.nonzero(self.state == 0)[0]

    @classmethod
    def from_state(cls, state):
        env = cls()
        env.state = state
        return env
