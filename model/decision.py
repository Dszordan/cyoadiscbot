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
            title,
            body,
            actions = [],
            id_ = str(shortuuid.ShortUUID().random(length=22))
        ):
        self.id_ = id_
        if self.id_ is None:
            self.id_ = str(shortuuid.ShortUUID().random(length=22))
        self.title = title
        self.body = body
        self.actions = actions
        self.voted_action = None
        self.state = DecisionState.PREPARATION
        self.publish_time = None
        self.resolve_time = None
        self.guild_id = None 
        self.message_id = None

    def get_next_decisions(self):
        """
            Return all the next Decisions associated with this Decisions actions
        """
        next_decisions = []
        for action in self.actions:
            if action.next_decision is not None:
                next_decisions.append(action.next_decision)
        return next_decisions

class ActionState(Enum):
    """
        The different states of a Action
        Proposal = The Action has been proposed by a player, but not yet reviewed by the DM.
        Approved = The Action has been approved by the DM and the published decision it is associated with will be updated.
        Denied = The Action has been denied by the DM.
        Published = An Action created by the DM and published with the associated Decision.
    """
    PROPOSED = 1
    APPROVED = 2
    DENIED = 3
    PUBLISHED = 4

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
            previous_decision = None,
            id_ = None,
            state = ActionState.PUBLISHED,
            author_id = None
        ):
        self.id_ = id_
        if self.id_ is None:
            self.id_ = str(shortuuid.ShortUUID().random(length=22))
        self.glyph = glyph
        self.description = description
        self.next_decision = next_decision
        self.previous_decision = previous_decision
        self.state = state
        self.author_id = author_id
    