"""
    Send messages to channels using embeds a little easier.
"""
from utils.embeds import CharacterEmbed, DefaultEmbed

class DecisionDisplayEmbed():
    """
        Display Decisions to a specific channel using Discord Embeds
    """

    def __init__(self, decision, ctx, channel):
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

        rich_body = '**' + decision.title + '**\n' + decision.body + '\n'
        for action in decision.actions:
            rich_body+=action.glyph + ' = ' + action.description + '\n'

        # create embed
        self.embed = CharacterEmbed(ctx)
        self.embed.description = rich_body

    async def send_message(self):
        """
            Send a message to the Channel found in self.channel
        """
        # Send embed
        decision_message = await self.channel.send(
            # content=rich_body,
            embed=self.embed)

        # Add reactions to embed
        for action in self.decision.actions:
            print(action.glyph + ' ' + action.description)
            await decision_message.add_reaction(action.glyph)

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
        await self.channel.send(
            # content=rich_body,
            embed=self.embed)