from utils.embeds import CharacterEmbed

class DecisionDisplay():

    def __init__(self, decision, ctx, channel):
        self.ctx = ctx
        self.channel = channel
        self.decision = decision

        rich_body = decision.body + '\n'
        for action in decision.actions:
            rich_body+=action['glyph'] + ' = ' + action['description'] + '\n'

        # create embed
        self.emb = CharacterEmbed(ctx)
        self.emb.description = rich_body

    async def send_message(self):
        # Send embed
        decision_message = await self.channel.send(
            # content=rich_body,
            embed=self.emb)

        # Add reactions to embed
        for action in self.decision.actions:
            print(action['glyph'] + ' ' + action['description'])
            await decision_message.add_reaction(action['glyph'])
