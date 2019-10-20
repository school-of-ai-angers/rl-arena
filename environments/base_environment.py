class BaseEnvironment:
    """
    This is the base class to encode a game
    """

    def reset(self):
        """
        Reset the game, returning:
        - the new state
        - the list of valid actions
        """
        raise NotImplementedError

    def step(self, action):
        """
        Apply the given action, returning:
        - the new state
        - the immediate reward of this action
        - a flag telling whether the game has finished
        - the list of valid actions
        """
        raise NotImplementedError

    def to_jsonable(self):
        """
        Return a representation of the current state that can be encoded as JSON.
        This will be used later to visually display the game state at each step
        """
        raise NotImplementedError

    @staticmethod
    def html_head():
        """
        Return HTML string to inject at the page's <head>
        """
        return ''

    @staticmethod
    def jsonable_to_html(jsonable):
        """
        Return a HTML representation of the game at the given state
        """
        raise NotImplementedError
