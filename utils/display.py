"""
    Send messages to channels using embeds a little easier.
"""
import datetime
from py_linq import Enumerable
from utils.embeds import CharacterEmbed, DefaultEmbed
from model.decision import ActionState

class DecisionDisplayEmbed():
    """
        Display Decisions to a specific channel using Discord Embeds
    """

    def __init__(self, decision, channel, ctx = None):
        """
            Set up a DecisionDisplay using the context of the calling action
            params:
                decision: The Decision to display
                ctx: The Discord Context that this display was called from
                channel: The channel intended to send the embed
        """
        self.ctx = ctx
        self.channel = channel
        self.decision = decision

        rich_body = '**' + decision.title + '**\n' + decision.body + '\n\n'
        rich_body+= '**Actions:**\n'
        for action in decision.actions:
            rich_body+=action.glyph + ' = ' + action.description + '\n'
        if decision.resolve_time:
            resolve_time_pretty = datetime.datetime.strftime(decision.resolve_time, "%d %b at %-I:%M %p")
            rich_body+= f'\nVoting closes at {resolve_time_pretty} \n'

        # create embed
        self.embed = CharacterEmbed(ctx)
        self.embed.description = rich_body

    async def send_message(self,
                           action_states = None):
        """
            Send a message to the Channel found in self.channel
        """
        # Send embed to channel
        decision_message = await self.channel.send(
            embed=self.embed)

        if not action_states:
            action_states = [ActionState.PUBLISHED, ActionState.APPROVED]
        all_actions = Enumerable(self.decision.actions)
        display_actions = all_actions.where(lambda x: x.state in action_states).to_list()

        # Add reactions to embed
        for action in display_actions:
            print(action.glyph + ' ' + action.description)
            await decision_message.add_reaction(action.glyph)
        
        return decision_message
    
class ActionDisplayEmbed():
    """
        Display Actions to a specific channel using Discord Embeds
    """

    def __init__(self, action, channel, ctx = None):
        """
            Set up an ActionDisplay using the context of the calling action
            params:
                action: The Action to display
                ctx: The Discord Context that this display was called from
                channel: The channel intended to send the embed
        """
        self.ctx = ctx
        self.channel = channel
        self.action = action

    async def send_message(self):
        """
            Send a message to the Channel found in self.channel
        """
        user = await self.ctx.bot.fetch_user(int(self.action.author_id))
        rich_body = f'Action Author: **{user.name}**\n\n'
        rich_body += f'**{self.action.glyph}** = **{self.action.description}**\n\n'

        # create embed
        self.embed = CharacterEmbed(self.ctx)
        self.embed.description = rich_body

        # Send embed
        action_message = await self.channel.send(
            embed=self.embed)
        
        return action_message

class GenericDisplayEmbed():
    """
        Display generic information to a specific channel using Discord embeds
        # TODO: Might make sense to make this a static method
        params:
            title: The title on the Discord Embed
            description: The description on the Discord Embed
            channel: The channel intended to send the embed
    """

    def __init__(self, title, description, channel):
        self.channel = channel
        self.description = description
        self.title = title
        self.embed = DefaultEmbed(title=title, description=description)

    async def send_message(self):
        """
            Send a message to the Channel found in self.channel
        """
        return await self.channel.send(
            # content=rich_body,
            embed=self.embed)