from environments.base_environment import BaseEnvironment
import numpy as np


class Environment(BaseEnvironment):
    def __init__(self):
        # Encode the board as 9 positions with -1 (empty), 0 or 1
        self.board = np.full((9,), -1)
        # The next player (0 or 1)
        self.player = 0
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
        self.board = np.full((9,), -1)
        return self.board, np.arange(9)

    def step(self, action):
        """
        Apply the given action, returning:
        - the new state
        - the immediate reward of this action
        - a flag telling whether the game has finished
        - the list of valid actions
        """
        # Play
        assert self.board[action] == -1
        self.board[action] = self.player

        # Check end of game
        for line in self.lines:
            marks = self.board[line]
            if marks[0] != -1 and marks[0] == marks[1] and marks[1] == marks[2]:
                # Current player won
                return self.board, 1, True, []
        if np.all(self.board != -1):
            # Tie
            return self.board, 0, True, []

        # Prepare next play
        self.player = (self.player + 1) % 2
        return self.board, 0, False, np.nonzero(self.board == -1)[0]

    def to_jsonable(self):
        """
        Return a representation of the current state that can be encoded as JSON.
        This will be used later to visually display the game state at each step
        """
        return self.board.tolist()

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
            if jsonable[i] == -1:
                return '&nbsp;'
            elif jsonable[i] == 0:
                return 'X'
            else:
                return 'O'

        return f'''
        <div id="tic-tac-toe-board">
            <table>
                <tr>
                    <td></td>
                    <td class="tic-tac-toe-vertical"></td>
                    <td></td>
                </tr>
                <tr>
                    <td class="tic-tac-toe-horizontal"></td>
                    <td class="tic-tac-toe-horizontal tic-tac-toe-vertical"></td>
                    <td class="tic-tac-toe-horizontal"></td>
                </tr>
                <tr>
                    <td></td>
                    <td class="tic-tac-toe-vertical"></td>
                    <td></td>
                </tr>
            </table>
        </div>
        '''
