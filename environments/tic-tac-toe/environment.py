from environments.base_environment import BaseEnvironment
import numpy as np


class Environment(BaseEnvironment):
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

    def to_jsonable(self):
        """
        Return a representation of the current state that can be encoded as JSON.
        This will be used later to visually display the game state at each step
        """
        return self.state.tolist()

    @staticmethod
    def html_head():
        """
        Return HTML string to inject at the page's <head>
        """
        return '<link rel="stylesheet" href="/static/environment-tic-tac-toe/style.css">'

    @staticmethod
    def jsonable_to_html(jsonable):
        """
        Return a HTML representation of the game at the given state
        """
        def get_square(i):
            if jsonable[i] == 0:
                return '&nbsp;'
            elif jsonable[i] == 1:
                return 'X'
            else:
                return 'O'

        return f'''
        <div class="tic-tac-toe-board">
            <table>
                <tr>
                    <td>{get_square(0)}</td>
                    <td class="tic-tac-toe-vertical">{get_square(1)}</td>
                    <td>{get_square(2)}</td>
                </tr>
                <tr>
                    <td class="tic-tac-toe-horizontal">{get_square(3)}</td>
                    <td class="tic-tac-toe-horizontal tic-tac-toe-vertical">{get_square(4)}</td>
                    <td class="tic-tac-toe-horizontal">{get_square(5)}</td>
                </tr>
                <tr>
                    <td>{get_square(6)}</td>
                    <td class="tic-tac-toe-vertical">{get_square(7)}</td>
                    <td>{get_square(8)}</td>
                </tr>
            </table>
        </div>
        '''
