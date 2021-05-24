from enum import Enum
class DecisionState(Enum):
    PREPARATION = 1
    DEPLOYED = 2
    RESOLVED = 3

class Decision:
    def __init__(self, id, body, actions):
        self.id = id
        self.body = body
        self.actions = actions
        self.state = DecisionState.PREPARATION
    