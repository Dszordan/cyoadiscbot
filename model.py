from enum import Enum
class decision_state(Enum):
    PREPARATION = 1
    DEPLOYED = 2
    RESOLVED = 3

class decision:
    def __init__(self, id, body, actions):
        self.id = id
        self.body = body
        self.actions = actions
        self.state = decision_state.PREPARATION
