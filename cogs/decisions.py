import asyncio

from discord import Emoji, PartialEmoji
from discord.ext import commands
import typing

from file_persistence import file_persistence
from model.decision import Decision, DecisionState
from utils.embeds import DefaultEmbed

class Decisions(commands.Cog):

    def __init__(self, bot, state_management: file_persistence):
        self.bot = bot
        self.state_management = state_management
    
    @commands.command(name='preparedecision')
    async def prepare_decision(self, ctx, body: str, *actions: typing.Union[Emoji, PartialEmoji, str]):
        parsed_actions = []
        rich_body = body + '\n'

        # Parse actions
        for action in actions:
            print(action)
            emoji = action.split('|')[0]
            description = action.split('|')[1]
            parsed_actions.append({
                'glyph': emoji,
                'description': description
            })
            rich_body+=emoji + ' = ' + description + '\n'

        # create decision model
        d = Decision(1, body, parsed_actions)
        self.state_management.write_state([d])
        
        # create embed
        emb = DefaultEmbed(ctx)
        emb.description = rich_body
        
        # Send embed
        decision_message = await ctx.channel.send(
            content=rich_body,
            embed=emb)

        # Add reactions to embed
        for action in parsed_actions:
            print(action['glyph'] + ' ' + action['description'])
            await decision_message.add_reaction(action['glyph'])

    @commands.command(name='viewdecisions')
    async def view_decisions(self, ctx, decision_state: str = DecisionState.PREPARATION):
        decisions = self.find_decisions(decision_state=decision_state)
        choices = []
        message_str = 'Found decision(s), which one do you want to view:'
        
        # If multiple decisions are found, list each and have user select one
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [{len(choices)}] {str(decision.body)[0:20]}'
        
        # Ensure selection is within the bounds of choice
        def check(m):
            return int(m.content) in [1,2,3,4] and m.channel == ctx.channel
        
        # Send choices, await a legitimate response
        await ctx.send(message_str)
        
        response = ''
        try:
            response = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            response = None

        # Display decision
        if response:
            display_decision = choices[int(msg.content) - 1]
            await ctx.send(f"Viewing {display_decision.id}, {display_decision.body} ")
        else:
            await ctx.send("Selection timed out or was canceled.")

    @commands.command(name='publishdecision')
    async def publish_decision(self, ctx, timeout: int):
        decisions = self.find_decisions(decision_state=DecisionState.PREPARATION)
        choices = []
        message_str = 'Found decision(s), which one do you want to publish:'
        
        # If multiple decisions are found, list each and have user select one
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [{len(choices)}] {str(decision.body)[0:20]}'
        
        # Ensure selection is within the bounds of choice
        def check(m):
            return int(m.content) in [1,2,3,4] and m.channel == ctx.channel
        
        # Send choices, await a legitimate response
        await ctx.send(message_str)
        
        response = ''
        try:
            response = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            response = None

        # Display decision
        if response:
            display_decision = choices[int(msg.content) - 1]
            decision_message = await ctx.send(f"Viewing {display_decision.id}, {display_decision.body} ")
            # Add reactions to embed
            for action in parsed_actions:
                print(action['glyph'] + ' ' + action['description'])
                await decision_message.add_reaction(action['glyph'])
        else:
            await ctx.send("Selection timed out or was canceled.")

    
    def find_decisions(self, id = None, decision_state = None):
        state = self.state_management.get_state()
        decisions = []

        if id:
            for decision in state:
                if decision.id == id:
                    return decision
        
        elif state:
            for decision in state:
                if decision.state == decision_state:
                    decisions.append(decision)
            return decisions
        
        else:
            return state