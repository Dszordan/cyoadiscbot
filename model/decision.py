"""
    Object models for Decisions and Actions
"""
from enum import Enum
import shortuuid

class DecisionState(Enum):
    """
        The different states of a Decision
        Preparation = The Decision is being edited by the DM and hasn't been published
        Published = The Decision has been delivered to a public channel to be voted on
        Resolved = The Decision has been voted on and voting is closed
    """
    PREPARATION = 1
    PUBLISHED = 2
    RESOLVED = 3

class Decision:
    """
        Simple object model for a Decision
        params:
            body: The body text of a Decision; flavour text
            actions: An array of Action objects
            id_: The UUID of the Decision
    """

    def __init__(
            self,
            body,
            actions,
            id_ = str(shortuuid.ShortUUID().random(length=22))
        ):
        self.id_ = id_
        if self.id_ is None:
            self.id_ = str(shortuuid.ShortUUID().random(length=22))
        self.body = body
        self.actions = actions
        self.state = DecisionState.PREPARATION

    def get_next_decisions(self):
        """
            Return all the next Decisions associated with this Decisions actions
        """
        next_decisions = []
        for action in self.actions:
            if action.next_decision is not None:
                next_decisions.append(action.next_decision)
        return next_decisions

class Action:
    """
        Simple object model for an Action
        params:
            glyph: The emoji representing the Action
            description: The description of the Action/emoji
            next_decision: The next Decision associated to this Action
            id_: The UUID of the Action
    """

    def __init__(
            self,
            glyph,
            description,
            next_decision = None,
            id_ = None
        ):
        self.id_ = id_
        if self.id_ is None:
            self.id_ = str(shortuuid.ShortUUID().random(length=22))
        self.glyph = glyph
        self.description = description
        self.next_decision = next_decision
    