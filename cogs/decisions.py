"""
    A Discord Cog that is a collection of commands related to managing Decisions.
"""
import asyncio
import datetime
import logging
import random

from discord.ext import commands
from discord.ext.commands import Context
from py_linq import Enumerable

from file_persistence import file_persistence
from model.decision import Decision, DecisionState
from utils.display import DecisionDisplayEmbed, GenericDisplayEmbed

class Decisions(commands.Cog):
    """
    A Discord Cog that is a collection of commands related to managing Decisions.
    params:
        bot: The bot that uses these commands.
        state_management: The state management object responsible for persisting
            Decisions' state.
    """
    def __init__(self,
                 bot: commands.Bot,
                 state_management: file_persistence):
        self.bot = bot
        self.state_management = state_management
        self.actions = self.bot.get_cog('Actions')
        self.user_interaction = self.bot.get_cog('UserInteraction')
        logging.basicConfig(level=logging.INFO)

    # Bot Commands
    @commands.command(name='preparedecision')
    async def prepare_decision(self,
                               ctx: Context,
                               title: str):
        """
        Prepare a new decision and persist it to state management.
        params:
            ctx: The context in which the command has been executed within.
            title: The title of the decision.
            body: The content of the decision.
        """
        # create decision model
        await GenericDisplayEmbed('Decision Body Update', 'What is the new body?', ctx.channel).send_message()
        body = await self.user_interaction.await_response(ctx)
        if not body:
            return
        decision = Decision(title, body)
        decision.guild_id = ctx.guild.id
        decisions = self.state_management.get_state()
        decisions['decisions'].append(decision)
        self.state_management.write_state(decisions)

        # Display decision
        await DecisionDisplayEmbed(decision, ctx.channel, ctx).send_message()
        
    @commands.command(name='modifydecision')
    async def modify_decision(self,
                              ctx: Context):
        """
        Receive a list of decisions and modify properties of one of them..
        params:
            ctx: The Discord context in which the command has been executed within.
        """
        selected_decision = await self.choose_decision(ctx, state=DecisionState.PREPARATION)
        if not selected_decision:
            return
        await DecisionDisplayEmbed(selected_decision, ctx.channel, ctx).send_message()
        
        # TODO: Add a way to delete a decision
        # TODO: Add a way to change the resolve time. Might not be able to do this, since the resolve time is set at publish time..
        message_str = "Which property do you wish to update? (c to cancel)\n"
        message_str += "[**1**] Title\n"
        message_str += "[**2**] Body\n"
        message_str += "[**3**] Actions\n"
        await GenericDisplayEmbed('Decision Property Update', message_str, ctx.channel).send_message()

        response = await self.user_interaction.await_response(ctx, ['1','2','3'])

        # Display decision
        if response:
            match response:
                case '1':
                    await GenericDisplayEmbed('Decision Title Update', 'What is the new title?', ctx.channel).send_message()
                    response = await self.user_interaction.await_response(ctx)
                    if response:
                        selected_decision.title = response
                        await self.update_decision(selected_decision)
                case '2':
                    await GenericDisplayEmbed('Decision Body Update', 'What is the new body?', ctx.channel).send_message()
                    response = await self.user_interaction.await_response(ctx)
                    if response:
                        selected_decision.body = response
                        await self.update_decision(selected_decision)
                case '3':
                    await self.actions.modify_actions(ctx, selected_decision)
            await DecisionDisplayEmbed(selected_decision, ctx.channel, ctx).send_message()

    @commands.command(name='viewdecisions')
    async def view_decisions(self,
                             ctx: Context,
                             decision_state: DecisionState = DecisionState.PREPARATION):
        """
        View stored decisions filtering on its state.
        params:
            ctx: The Discord context in which the command has been executed within.
            decision_state: The state to filter decisions on.
        """
        decisions = self.find_decisions(guild_id=ctx.guild.id, decision_state=decision_state)
        if not decisions:
            await ctx.send(f"No decisions found with the state {decision_state}.")
            return
        choices = []
        message_str = 'Found Decision(s), which one do you want to view. (c to cancel):'

        # If multiple decisions are found, list each and have user select one
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [**{len(choices)}**] {str(decision.title)[0:20]}'

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
    async def publish_decision(self,
                               ctx: Context,
                               timeout: int = 120):
        """
        Changes a Decision to the PUBLISHED state and delivers the Decision to the publish channel.
        :param ctx: The Discord context in which the command has been executed within.
        :param timeout: The amount of time that the Decision can be voted upon.
        :return: None
        """
        # Find all Decisions in the PREPARATION state
        choices = []
        admin_state = self.state_management.get_admin_state()
        publish_channel = admin_state['channels']['publish']

        selected_decision = await self.choose_decision(ctx, state=DecisionState.PREPARATION)
        if not selected_decision:
            await ctx.send('No decisions found in that state.')
            return
        # # Display choices
        # message_str = "Found decision(s), which one do you want to publish:\n"
        # for i, decision in enumerate(decisions):
        #     choices.append(decision)
        #     message_str += f"[**{i+1}**] {str(decision.title)[0:20]}\n"
        # message_str += f"Type a number between 1 and {len(choices)} to select a decision, or type 'c' to cancel."
        # await GenericDisplayEmbed('Multiple Decisions Found', message_str, ctx.channel).send_message()

        # response = await self.user_interaction.await_response(ctx, [str(i) for i in range(1, len(choices) + 1)] + ["c"])

        # Publish selected decision
        # if not response:
        #     return
        
        # selected_decision = choices[int(response) - 1]
        await DecisionDisplayEmbed(selected_decision, ctx, ctx.channel).send_message()

        # Confirm publication
        message = f"Do you wish to publish the above Decision to **{publish_channel}**?\n" + \
            f"[**y**] = Publish this decision to **{publish_channel}**\n" + \
            f"[**n**] = Continue editing the Decision"
        await GenericDisplayEmbed('Confirm Publication', message, ctx.channel).send_message()
        response = await self.user_interaction.await_response(ctx, ['y','n','c'])
        
        if not response:
            return
        if response.lower() == 'n':
            await ctx.send('Canceled operation.')

        # Let the user choose a number of minutes from now to resolve the decision
        message_str = 'How many minutes from now do you want to resolve the decision at?'
        await GenericDisplayEmbed('Choose Resolve Time', message_str, ctx.channel).send_message()
        response = await self.user_interaction.await_response(ctx)
        resolve_time = datetime.datetime.now() + datetime.timedelta(minutes=int(response))

        resolve_time_pretty = datetime.datetime.strftime(resolve_time, "%d %b at %-I:%M %p")
        message_str = f'The decision will resolve at the following time: **{resolve_time_pretty}**. Is this correct? (y/n)'
        await GenericDisplayEmbed('Resolve Time', message_str, ctx.channel).send_message()
        response = await self.user_interaction.await_response(ctx, ['y','n','c'])

        if response.lower() == 'n':
            await ctx.send('Canceled operation.')
        if not response or response.lower() == 'n':
            return

        # Find the 'public-channel' and display the decision
        channel = next((x for x in ctx.guild.channels if x.name == publish_channel), None)
        selected_decision.publish_time = str(datetime.datetime.now())
        selected_decision.resolve_time = resolve_time
        selected_decision.state = DecisionState.PUBLISHED
        await ctx.send(f'The decision will publish to {channel} with a resolve time at {selected_decision.resolve_time}')
        sent_message = await DecisionDisplayEmbed(selected_decision, channel, ctx).send_message()
        selected_decision.message_id = sent_message.id
        await self.update_decision(selected_decision)

    # Helper Functions
    async def update_decision(self,
                              decision: Decision):
        self.state_management.update_decision(decision)
      
    async def check_time(self):
        """ Checks the time for each published decision and checks if the resolve time is up """
        decisions = self.find_decisions(decision_state=DecisionState.PUBLISHED)
        for decision in decisions:
            if decision.resolve_time and (decision.resolve_time < datetime.datetime.now()):
                logging.info(f'Resolve time is up for {decision.id_}, {decision.title}')
                guild = self.bot.get_guild(decision.guild_id)
                publish_channel_name = self.state_management.get_admin_state()['channels']['publish']
                dm_channel_name = self.state_management.get_admin_state()['channels']['dm']
                logging.info(f'Publish channel name: {publish_channel_name}, DM channel name: {dm_channel_name}`')
                publish_channel = next((x for x in guild.channels if x.name == publish_channel_name), None)
                dm_channel = next((x for x in guild.channels if x.name == dm_channel_name), None)
                logging.info(f'Publish channel: {publish_channel.name}')

                # Find the specific discord message object
                message = await publish_channel.fetch_message(decision.message_id)
                # Get the message reaction count from the message
                reactions = message.reactions
                # Tally the reactions and find the reaction with the most votes
                top_reaction = None
                for reaction in reactions:
                    if not top_reaction:
                        top_reaction = reaction
                    elif reaction.count > top_reaction.count:
                        top_reaction = reaction
                
                # TODO: Handle the case where there is a tie
                # TODO: Handle the case where there is no reaction
                # Find the action that corresponds to the reaction
                action = next((x for x in decision.actions if x.glyph == top_reaction.emoji), None)
                # set the found action as the voted action
                decision.voted_action = action
                
                decision.state = DecisionState.RESOLVED
                await self.update_decision(decision)
                # Get the message reaction count from the message
                

                # create list of messages
                list_of_messages = ["The people have spoken.",
                                    "A fate is drawn.",
                                    "The gods deign.",
                                    "A decision has been made.",
                                    "The future crystalizes."]
                # TODO: Make the message embed look nicer
                message = random.choice(list_of_messages)
                await GenericDisplayEmbed(message, f'An action has been chosen \n{action.glyph}: {action.description}', publish_channel).send_message()
                await GenericDisplayEmbed(message, f'An action has been chosen \n{action.glyph}: {action.description}', dm_channel).send_message()

    async def choose_decision(self,
                              ctx: Context,
                              state: DecisionState):
        """
        choose_decision: Display a list of decisions and allow the user to select one.
        params:
            ctx: The Discord context in which the command has been executed within.
            state: The state of the decision to choose from.
        """
        decisions = self.find_decisions(guild_id=ctx.guild.id, decision_state=state)
        choices = []
        if not decisions:
            return None

        # If multiple decisions are found, list each and have user select one
        message_str = 'Found Decision(s), which one do you want to select. (c to cancel):'
        for decision in decisions:
            choices.append(decision)
            message_str += f'\n [**{len(choices)}**] {str(decision.title)[0:20]}'

        # Send choices, await a legitimate response
        await GenericDisplayEmbed('Select Decision', message_str, ctx.channel).send_message()

        response = await self.user_interaction.await_response(ctx, 
            [str(v) for v in range(1, len(choices) + 1)] + ["c"])

        # Display decision
        if response:
            selected_decision = choices[int(response) - 1]
            logging.info(f'Selected decision: {selected_decision}')
            return selected_decision
        return None

    def find_decisions(self,
                       decision_id: str = None,
                       decision_state: DecisionState = None,
                       guild_id: str = None):
        """
        Find a Decision in state management based on filter criteria.
        params:
            id: The unique identifier of a Decision to filter the results with.
            decision_state: The state of Decisions to filter the results with.
            guild_id: The guild id of the decision to filter the results with.
        """
        state = self.state_management.get_state()
        state_enumerable = Enumerable(state['decisions'])
        logging.info(f'Finding decisions with id: {decision_id}, state: {decision_state}, guild_id: {guild_id}')

        # If an id is provided, return the decision with that id
        if decision_id:
            decision = state_enumerable.where(lambda x: x.id_ == decision_id).first_or_default()
            logging.info(f'Found decision: {decision}')
            return decision
                # TODO: Handle scenario where none are found of this id
        # If no id is provided, return all decisions with the provided state
        elif decision_state:
            if guild_id:
                state_enumerable = state_enumerable.where(lambda x: x.guild_id == guild_id)
            state_enumerable = state_enumerable.where(lambda x: x.state == decision_state)
            logging.info(f'Found decisions: {state_enumerable}')
                # TODO: Handle scenario where none are found of this state
            return state_enumerable
        return None
  
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
