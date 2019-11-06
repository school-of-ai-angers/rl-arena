from environments.base_environment import BaseEnvironment
import numpy as np


def _pos(i, j):
    return 7 * i + j


rows = [
    [_pos(line, col_start+k) for k in range(4)]
    for line in range(6)
    for col_start in range(4)
]
columns = [
    [_pos(line_start+k, col) for k in range(4)]
    for line_start in range(3)
    for col in range(7)
]
diagonals_1 = [
    [_pos(line_start+k, col_start+k) for k in range(4)]
    for line_start in range(3)
    for col_start in range(4)
]
diagonals_2 = [
    [_pos(line_start+k, col_start-k) for k in range(4)]
    for line_start in range(3)
    for col_start in range(3, 7)
]


class Environment(BaseEnvironment):

    lines = rows + columns + diagonals_1 + diagonals_2

    def __init__(self):
        # Encode the board as 42 positions with 0 (empty), 1 (first player) or -1 (second player).
        # The position at line `i` and column `j` will be at `7*i+j`.
        # The 43-th position is the current player (-1 or 1)
        self.state = np.zeros((43,))

    def reset(self):
        self.state[:42] = 0
        self.state[42] = 1
        return self.state, list(range(7))

    def step(self, action):
        assert self.state[_pos(0, action)] == 0, 'Invalid action'

        # Put the piece on the board
        for i in reversed(range(6)):
            if self.state[_pos(i, action)] == 0:
                pos = _pos(i, action)
                self.state[pos] = self.state[42]
                break

        # Check for win
        for pos_s in self.lines:
            if pos in pos_s:
                values = self.state[pos_s]
                if np.all(values == 1) or np.all(values == -1):
                    return self.state, 1, True, []

        # Check for draw
        if np.all(self.state != 0):
            return self.state, 0, True, []

        # update list of possible actions
        self.state[42] = -self.state[42]
        return self.state, 0, False, np.nonzero(self.state[[_pos(0, k) for k in range(7)]] == 0)[0]

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
        return '<link rel="stylesheet" href="/static/environment-connect-four/style.css">'

    @staticmethod
    def jsonable_to_html(jsonable):
        """
        Return a HTML representation of the game at the given state
        """

        # Detect winning line
        state = np.asarray(jsonable)
        win_cells = []
        for pos_s in Environment.lines:
            values = state[pos_s]
            if np.all(values == 1) or np.all(values == -1):
                win_cells = pos_s
                break

        # Build board
        lines_html = [
            '<tr>' + ''.join(
                f'<td class="connect-four-{int(state[_pos(line, col)])} \
                    {"connect-four-win-line" if _pos(line, col) in win_cells else ""}"></td>'
                for col in range(7)
            ) + '</tr>'
            for line in range(6)
        ]
        table_html = '\n'.join(lines_html)

        return f'''
        <table class="connect-four-board {"connect-four-board-win" if len(win_cells) else ""}">
            {table_html}
        </table>
        '''
