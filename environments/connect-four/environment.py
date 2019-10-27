from environments.base_environment import BaseEnvironment
import numpy as np

rows = [
    (np.full(4, line), np.arange(col_start, col_start+4))
    for line in range(6)
    for col_start in range(4)
]
columns = [
    (np.arange(line_start, line_start+4), np.full(4, col))
    for line_start in range(3)
    for col in range(7)
]
diagonals_1 = [
    (np.arange(line_start, line_start+4), np.arange(col_start, col_start+4))
    for line_start in range(3)
    for col_start in range(4)
]
diagonals_2 = [
    (np.arange(line_start, line_start+4), np.arange(col_start, col_start-4, -1))
    for line_start in range(3)
    for col_start in range(3, 7)
]


class Environment(BaseEnvironment):

    lines = rows + columns + diagonals_1 + diagonals_2

    def __init__(self):
        # 0 = empty, 1 = player 1, 2 = player 2
        self.board_state = np.zeros((6, 7))
        self.player = 1

    def reset(self):
        self.board_state = np.zeros((6, 7))
        self.player = 1
        return self.board_state, list(range(7))

    def step(self, action):
        assert self.board_state[0, action] == 0, 'Invalid action'

        # Put the piece on the board
        for i in reversed(range(6)):
            if self.board_state[i, action] == 0:
                self.board_state[i, action] = self.player
                break

        # Check for win
        for i_s, j_s in self.lines:
            if i in i_s and action in j_s:
                values = self.board_state[i_s, j_s]
                if np.all(values == 1) or np.all(values == 2):
                    return self.board_state, 1, True, []

        # Check for draw
        if np.all(self.board_state != 0):
            return self.board_state, 0, True, []

        # update list of possible actions
        self.player = 2 if self.player == 1 else 1
        return self.board_state, 0, False, np.nonzero(self.board_state[0, :] == 0)[0]

    def to_jsonable(self):
        """
        Return a representation of the current state that can be encoded as JSON.
        This will be used later to visually display the game state at each step
        """
        return self.board_state.flatten().tolist()

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
        state = np.asarray(jsonable).reshape((6, 7))
        win_cells = []
        for i_s, j_s in Environment.lines:
            values = state[i_s, j_s]
            if np.all(values == 1) or np.all(values == 2):
                win_cells = list(zip(i_s, j_s))
                break

        # Build board
        lines_html = [
            '<tr>' + ''.join(
                f'<td class="connect-four-{int(state[line, col])} \
                    {"connect-four-win-line" if (line, col) in win_cells else ""}"></td>'
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
