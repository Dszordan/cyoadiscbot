"""
    A Discord Cog that is a collection of commands related to managing Decisions.
"""
import asyncio
import datetime
import typing

from discord import Emoji, PartialEmoji
from discord.ext import commands

from file_persistence import file_persistence
from model.decision import Decision, DecisionState, Action
from utils.display import DecisionDisplayEmbed, GenericDisplayEmbed

class Decisions(commands.Cog):
    """
    A Discord Cog that is a collection of commands related to managing Decisions.
    params:
        bot: The bot that uses these commands.
        state_management: The state management object responsible for persisting
            Decisions' state.
    """
    def __init__(self, bot, state_management: file_persistence):
        self.bot = bot
        self.state_management = state_management

    @commands.command(name='preparedecision')
    async def prepare_decision(
        self, ctx, body: str, *actions: typing.Union[Emoji, PartialEmoji, str]):
        """
        Prepare a new decision and persist it to state management.
        params:
            ctx: The context in which the command has been executed within.
            body: The content to put in the decision
            actions: The emojis that make up the reactions to the decision,
                In the form emoji|description emoji|description
        """
        parsed_actions = []

        # Parse actions
        for action in actions:
            print(action)
            emoji = action.split('|')[0]
            description = action.split('|')[1]
            parsed_actions.append(Action(emoji, description))

        # create decision model
        decision = Decision(body, parsed_actions)
        self.state_management.write_state([decision])

        # Display decision
        await DecisionDisplayEmbed(decision, ctx, ctx.channel).send_message()

    @commands.command(name='viewdecisions')
    async def view_decisions(self, ctx, decision_state: str = DecisionState.PREPARATION):
        """
        View stored decisions filtering on its state.
        params:
            ctx: The Discord context in which the command has been executed within.
            decision_state: The state to filter decisions on.
        """
        decisions = self.find_decisions(decision_state=decision_state)
        choices = []
        message_str = 'Found Decision(s), which one do you want to view. (c to cancel):'

        # If multiple decisions are found, list each and have user select one
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [**{len(choices)}**] {str(decision.body)[0:20]}'

        # Ensure selection is within the bounds of choice
        def check(msg):
            valid = [str(v) for v in range(1, len(choices) + 1)] + ["c"]
            return msg.channel == ctx.channel \
                and msg.author == ctx.author \
                and msg.content.lower() in valid

        # Send choices, await a legitimate response
        await GenericDisplayEmbed('Multiple Matches Found', message_str, ctx.channel).send_message()

        response = ''
        try:
            response = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            response = None

        # Display decision
        if response:
            if response.content == 'c':
                response = None
            else:
                display_decision = choices[int(response.content) - 1]
                await DecisionDisplayEmbed(display_decision, ctx, ctx.channel).send_message()
        if response is None:
            await ctx.send("Selection timed out or was canceled.")

    @commands.command(name='publishdecision')
    async def publish_decision(self, ctx, timeout: int = 120):
        """
        TODO: Implement timeout
        Change a Decision to the PUBLISHED state and deliver the Decision to the publish channel.
        params:
            ctx: The Discord context in which the command has been executed within.
            timeout: The amount of time that the Decision can be voted upon.
        """
        decisions = self.find_decisions(decision_state=DecisionState.PREPARATION)
        choices = []
        message_str = 'Found decision(s), which one do you want to publish:'
        publish_channel = 'public-channel'

        # If multiple decisions are found, list each and have user select one
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [**{len(choices)}**] {str(decision.body)[0:20]}'

        # Ensure selection is within the bounds of choice
        def check(msg):
            valid = [str(v) for v in range(1, len(choices) + 1)] + ["c"]
            return msg.channel == ctx.channel \
                and msg.author == ctx.author \
                and msg.content.lower() in valid

        # Send choices, await a legitimate response
        await GenericDisplayEmbed('Multiple Decisions Found',
                                    message_str, ctx.channel).send_message()

        response = ''
        try:
            response = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            response = None

        # Display decision
        if response:
            display_decision = choices[int(response.content) - 1]
            await DecisionDisplayEmbed(display_decision, ctx, ctx.channel).send_message()

            def publish_check(msg):
                return msg.content in ['y','n'] and msg.channel == ctx.channel

            message = f"Do you wish to publish the above Decision to **{publish_channel}**?" + \
                f"\n [**y**] = Publish this decision to **{publish_channel}**."  + \
                "\n [**n**] = Continue editing the Decision."
            await GenericDisplayEmbed('Confirm Publication', message, ctx.channel).send_message()
            publish_response = ''
            try:
                publish_response = await self.bot.wait_for(
                    "message", timeout=30, check=publish_check)
            except asyncio.TimeoutError:
                publish_response = None

            if publish_response.content:
                if publish_response.content == 'y':
                    channel = next(
                        (x for x in ctx.guild.channels if x.name == publish_channel), None)
                    await DecisionDisplayEmbed(display_decision, ctx, channel).send_message()
                    # TODO: set state of decision to published
                else:
                    publish_response = None
            if publish_response is None:
                await ctx.send('Selection timed out or was canceled.')

        else:
            await ctx.send("Selection timed out or was canceled.")

    def find_decisions(self, decision_id = None, decision_state = None):
        """
        Find a Decision in state management based on filter criteria.
        params:
            id: The unique identifier of a Decision to filter the results with.
            decision_state: The state of Decisions to filter the results with.
        """
        state = self.state_management.get_state()
        decisions = []

        if decision_id:
            for decision in state:
                if decision.id == decision_id:
                    return decision
                # TODO: Handle scenario where none are found of this id

        elif decision_state:
            for decision in state:
                if decision.state == decision_state:
                    decisions.append(decision)
                # TODO: Handle scenario where none are found of this state
            return decisions

        else:
            return state

    @commands.command(name='pt')
    async def pt(self, ctx, timeout: int = 120):
        """
        Change a Decision to the PUBLISHED state and deliver the Decision to the publish channel.
        params:
            ctx: The Discord context in which the command has been executed within.
            timeout: The amount of time that the Decision can be voted upon.
        """
        choices = []
        dates = [
            datetime.datetime.now(),
            datetime.datetime.now()+datetime.timedelta(minutes=30),
            datetime.datetime.now()+datetime.timedelta(minutes=60),
            datetime.datetime.now()+datetime.timedelta(minutes=90),
            datetime.datetime.now()+datetime.timedelta(minutes=120),
        ]
        message_str = 'What time do you want to publish at?'

        # If multiple decisions are found, list each and have user select one
        for date in dates:
            rounded_date = round_time(date,datetime.timedelta(minutes=30), to='up')
            choices.append(rounded_date)
            message_str += f'\n [**{len(choices)}**] {str(rounded_date)}'

        await GenericDisplayEmbed('Time', message_str, ctx.channel).send_message()

def round_time(date=None, date_delta=datetime.timedelta(minutes=1), to='average'):
    """
    Round a datetime object to a multiple of a timedelta
    date : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    from:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    round_to = date_delta.total_seconds()
    if date is None:
        date = datetime.datetime.now()
    seconds = (date - date.min).seconds

    if seconds % round_to == 0 and date.microsecond == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            # // is a floor division, not a comment on following line (like in javascript):
            rounding = (seconds + date.microsecond/1000000 + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return date + datetime.timedelta(0, rounding - seconds, - date.microsecond)
