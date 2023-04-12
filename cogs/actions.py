"""
    A Discord Cog that is a collection of commands related to managing Decisions.
"""
import logging

from discord import Emoji, PartialEmoji, Embed
from discord.ext import commands
from discord.ext.commands import Context
from py_linq import Enumerable

from file_persistence import file_persistence
from model.decision import Decision, DecisionState, Action, ActionState
from utils.display import ActionDisplayEmbed, DecisionDisplayEmbed, GenericDisplayEmbed

class Actions(commands.Cog):
    def __init__(self, bot, persistence: file_persistence):
        logging.basicConfig(level=logging.INFO)
        self.bot = bot
        self.persistence = persistence
        self.decisions = self.bot.get_cog('Decisions')
        self.user_interaction = self.bot.get_cog('UserInteraction')

    @commands.command(name='reviewactions')
    async def review_actions(self,
                             ctx: Context):
        """
        Receive a list of proposed actions and modify properties of one of them.
        params:
            ctx: The Discord context in which the command has been executed within.
        """
        logging.info("Reviewing actions.")
        await ctx.send("Reviewing proposed actions.")
        selected_action = await self.choose_action(ctx, ActionState.PROPOSED)
        logging.info(f"found proposed actions, {selected_action}")
        if not selected_action:
            ctx.send("Found no proposed actions to review.")
            return

        decision = selected_action.previous_decision
        decision.actions.append(selected_action)

        # display proposed action
        await ActionDisplayEmbed(selected_action, ctx.channel, ctx).send_message()
        await ctx.send("This action would apply to the following decision.")

        # display associated decision
        await DecisionDisplayEmbed(selected_action.previous_decision, ctx.channel, ctx).send_message()
        
        # prompt user to approve or deny the action
        str_message = "Approve the proposed action and update the already published decision?\n"
        str_message += "Type 'y' to approve, 'n' to decline the proposal entirely, or 'c' to cancel."
        await ctx.send(str_message)
        response = await self.user_interaction.await_response(ctx, ['y', 'n'])
        if not response:
            return
        
        user_response = ""
        if response == 'n':
            await ctx.send("Action denied.")
            selected_action.state = ActionState.DENIED
            await self.decisions.update_decision(decision)
        if response == 'y':
            await ctx.send("Action approved.")
            selected_action.state = ActionState.APPROVED
            await self.decisions.update_decision(decision)  

            # Find the specific discord message object and update it
            guild = self.bot.get_guild(decision.guild_id)
            publish_channel_name = self.persistence.get_admin_state()['channels']['publish']
            publish_channel = next((x for x in guild.channels if x.name == publish_channel_name), None)
            message = await publish_channel.fetch_message(decision.message_id)
            updated_embed = DecisionDisplayEmbed(decision, ctx.author, ctx)
            await message.edit(embed=updated_embed.embed)
            await message.add_reaction(selected_action.glyph)

        # DM the user who created the action about the result
        user = self.bot.get_user(selected_action.author_id)
        await user.send(f"Your action proposal {selected_action.glyph} = {selected_action.description} has been reviewed by the DM. The result is: {response == 'y' and 'approved' or 'denied'}.")

    @commands.command(name='createaction')
    async def create_action(self,
                             ctx: Context,
                             channel = None,
                             decision: Decision = None):
        """
        Create an action for a decision.
        params:
            ctx: The Discord context in which the command has been executed within.
            channel: The channel to send the action to. If not provided, the channel of the context will be used.
            decision: The decision to modify actions for. If not provided, the user will be prompted to select one.
        """
        # Need to find a way to support both a channel and a DM
        # Get away from passing around CTX and instead deal with channels / members
        logging.info(f'Creating action for decision {decision}')
        if not channel:
            channel = ctx.channel
        
        selected_decision = decision
        if not decision:
            selected_decision = await self.decisions.choose_decision(ctx, DecisionState.PREPARATION)

        if not selected_decision:
            await channel.send('Before an action can be created, a decision needs to be prepared. Create a decision first.')
            return
        
        message_str = 'Describe the action. (c to cancel)\n'
        await GenericDisplayEmbed('Create Action', message_str, channel).send_message()
        action_description = await self.user_interaction.await_response(ctx, channel=channel)
        if not action_description:
            return None
        
        message_str = 'Give the action a glyph/emoji (c to cancel)\n'
        await GenericDisplayEmbed('Create Action', message_str, channel).send_message()
        action_glyph = await self.user_interaction.await_response(ctx, channel=channel)
        if not action_glyph:
            return None
        
        new_action = Action(glyph=action_glyph, description=action_description, previous_decision=selected_decision)
        selected_decision.actions.append(new_action)
        await DecisionDisplayEmbed(selected_decision, channel, ctx).send_message()
        message_str = 'Does this look good? (y/n)\n'
        await GenericDisplayEmbed('Create Action', message_str, channel).send_message()
        response = await self.user_interaction.await_response(ctx, ['y', 'n'], timeout=30, channel=channel)
        if not response:
            return None
        if response == 'n':
            await channel.send(f'Action creation cancelled.')
            return None

        await self.decisions.update_decision(selected_decision)
        return new_action

    @commands.command(name='modifyactions')
    async def modify_actions(self,
                             ctx: Context,
                             decision: Decision = None):
        """
        Receive a list of decisions and modify properties of one of them.
        params:
            ctx: The Discord context in which the command has been executed within.
            decision: The decision to modify actions for. If not provided, the user will be prompted to select one.
        """
        selected_decision = decision
        if not decision:
            selected_decision = await self.decisions.choose_decision(ctx, DecisionState.PREPARATION)
        
        message_str = 'Which action do you want to modify? (c to cancel)\n'
        choices = []
        for index, action in enumerate(selected_decision.actions):
            choices.append(action)
            message_str += f'[**{index + 1}**] {action.glyph} = {action.description} \n'
        message_str += '[**n**] Create new action.\n'
        await GenericDisplayEmbed('Modify Action', message_str, ctx.channel).send_message()

        response = await self.user_interaction.await_response(ctx, [str(v) for v in range(1, len(selected_decision.actions) + 1)] + ['n', 'c'])
        if response:
            if response == 'n':
                logging.info(f'Creating new action for decision {selected_decision}.')
                await self.create_action(ctx, decision=selected_decision)
            else:
                selected_action = choices[int(response) - 1]
                await self.update_action(ctx, selected_decision, selected_action)

    @commands.command(name='proposeaction')
    async def propose_action(self,
                            ctx: Context):
        """
        Propose an action to a decision.
        params:
            ctx: The Discord context in which the command has been executed within.
        """
        # DM the user who called the command
        published_decisions = self.decisions.find_decisions(decision_state=DecisionState.PUBLISHED, guild_id=ctx.guild.id)
        selected_decision = None
        if not published_decisions:
            await ctx.author.send('Unfortunately there are no published decisions to propose an action to. Wait until a decision has been published first!')
            return
        if len(published_decisions) > 1:
            await ctx.author.send('There are multiple published decisions. Please select one of the following:')
            selected_decision = await self.decisions.choose_decision(ctx, state=DecisionState.PUBLISHED)
        else:
            selected_decision = published_decisions[0]
        await ctx.author.send(f'Hey there {ctx.author.name}, I\'m responding to your action proposal. Let\'s create a new action.')
                
        message_str = 'Describe the action. (c to cancel)\n'
        await GenericDisplayEmbed('Propose Action', message_str, ctx.author).send_message()
        action_description = await self.user_interaction.await_response(ctx, channel=ctx.author)
        if not action_description:
            return None
        
        message_str = 'Give the action a glyph/emoji (c to cancel)\n'
        await GenericDisplayEmbed('Propose Action', message_str, ctx.author).send_message()
        action_glyph = await self.user_interaction.await_response(ctx, channel=ctx.author)
        if not action_glyph:
            return None
        
        new_action = Action(glyph=action_glyph, description=action_description, previous_decision=selected_decision, action_state=ActionState.PROPOSED, author_id=ctx.author.id)
        selected_decision.actions.append(new_action)
        await DecisionDisplayEmbed(selected_decision, ctx.author, ctx).send_message()
        message_str = 'Does this look good? (y/n)\n If so, the action will be sent to the DM to be approved.\n'
        await GenericDisplayEmbed('Propose Action', message_str, ctx.author).send_message()
        response = await self.user_interaction.await_response(ctx, ['y', 'n'], timeout=30, channel=ctx.author)
        if not response:
            return None
        if response == 'n':
            await ctx.author.send(f'Action creation cancelled.')
            return None

        await self.decisions.update_decision(selected_decision)

        # need republish or update them embed AND add an action to the decision
        guild = self.bot.get_guild(selected_decision.guild_id)
        dm_channel_name = self.persistence.get_admin_state()['channels']['dm']
        dm_channel = next((x for x in guild.channels if x.name == dm_channel_name), None)

        # Send the action to the DM
        message_str = "A new action has been proposed for the following decision:\n"
        message_str += f'{selected_decision.title}\n'
        message_str += f'{selected_decision.body}\n'
        message_str += f'Proposed by: {ctx.author.name}\n'
        message_str += f'Action: {new_action.glyph} = {new_action.description}\n'
        message_str += f'Please react with \U0001F44D to approve or \U0001F44E to reject.\n'
        message = await GenericDisplayEmbed('Action Proposal', message_str, dm_channel).send_message()
        await message.add_reaction('\U0001F44D')
        await message.add_reaction('\U0001F44E')



    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return
        if reaction.message.channel.name == self.persistence.get_admin_state()['channels']['dm']:
            # Find the decision that this action belongs to
            logging.info(f'Action reaction received: {reaction.emoji} in channel {reaction.message.channel.name}')
            # if reaction message body contains 'Action Proposal'
            if 'new action has been proposed' in reaction.message.embeds[0].description:
                logging.info(f'Action reaction received: {reaction.emoji} in channel {reaction.message.channel.name}')
                # TODO: Find a way to get the decision from the message
                
                # if reaction.emoji == '\U0001F44D':
                #     action.action_state = ActionState.APPROVED
                #     await self.decisions.update_decision(decision)
                #     await reaction.message.channel.send(f'Action {action.glyph} = {action.description} has been approved.')
                #     await self.publish_decision(reaction.message.channel, decision)
                # elif reaction.emoji == '\U0001F44E':
                #     action.action_state = ActionState.REJECTED
                #     await self.decisions.update_decision(decision)
                #     await reaction.message.channel.send(f'Action {action.glyph} = {action.description} has been rejected.')
                #     await self.publish_decision(reaction.message.channel, decision)
                # else:
                #     logging.error(f'Unknown reaction {reaction.emoji}')
            # decision = self.decisions.find_decision_by_message_id(reaction.message.id)
            # if not decision:
            #     logging.error(f'Could not find decision for message {reaction.message.id}')
            #     return
            # action = next((x for x in decision.actions if x.glyph == reaction.emoji), None)
            # if not action:
            #     logging.error(f'Could not find action for reaction {reaction.emoji}')
            #     return

    @commands.command(name='updateaction')
    async def update_action(self,
                             ctx: Context,
                             decision: Decision = None,
                             action: Action = None):
        """
        Update an action for a decision.
        params:
            ctx: The Discord context in which the command has been executed within.
            decision: The decision to modify actions for. If not provided, the user will be prompted to select one.
            action: The action to update. If not provided, the user will be prompted to select one.
        """
        selected_decision = decision
        if not decision:
            selected_decision = await self.decisions.choose_decision(ctx, DecisionState.PREPARATION)
        
        selected_action = action
        if not action:
            message_str = 'Which action do you want to update? (c to cancel)\n'
            choices = []
            for index, action in enumerate(selected_decision.actions):
                choices.append(action)
                message_str += f'[**{index + 1}**] {action.glyph} = {action.description} \n'
            await GenericDisplayEmbed('Update Action', message_str, ctx.channel).send_message()

            response = await self.user_interaction.await_response(ctx, [str(v) for v in range(1, len(selected_decision.actions) + 1)] + ['c'])
            if response:
                selected_action = choices[int(response) - 1]
            else:
                return
        message_str = 'Describe the action. (c to cancel)\n'
        await GenericDisplayEmbed('Update Action', message_str, ctx.channel).send_message()
        action_description = await self.user_interaction.await_response(ctx)
        
        message_str = 'Give the action a glyph/emoji (c to cancel)\n'
        await GenericDisplayEmbed('Update Action', message_str, ctx.channel).send_message()
        action_glyph = await self.user_interaction.await_response(ctx)

        # Find action and update
        action_index = -1
        for index, act in enumerate(selected_decision.actions):
            if act.id_ == selected_action.id_:
                action_index = index
        if action_index != -1:
            selected_decision.actions[action_index].description = action_description
            selected_decision.actions[action_index].glyph = action_glyph
            selected_decision.actions[action_index].previous_decision = selected_decision
            await self.decisions.update_decision(selected_decision)
        else:
            logging.error('could not find that action to update.')

    async def choose_action(self,
                              ctx: Context,
                              state: ActionState):
        """
        choose_action: Display a list of actions and allow the user to select one.
        params:
            ctx: The Discord context in which the command has been executed within.
            state: The state of the action to choose from.
        """
        actions = await self.find_actions(guild_id=ctx.guild.id, action_state=state)
        choices = []
        if not actions:
            return None

        # If multiple actions are found, list each and have user select one
        message_str = 'Found Action(s), which one do you want to select. (c to cancel):'
        for action in actions:
            choices.append(action)
            message_str += f'\n [**{len(choices)}**] {action.glyph} {str(action.description)[0:20]} for decision **{action.previous_decision.title}**'

        # Send choices, await a legitimate response
        await GenericDisplayEmbed('Select action', message_str, ctx.channel).send_message()

        response = await self.user_interaction.await_response(ctx, 
            [str(v) for v in range(1, len(choices) + 1)] + ["c"])

        # Display action
        if response:
            selected_action = choices[int(response) - 1]
            logging.info(f'Selected action: {selected_action}')
            return selected_action
        return None

    async def find_actions(self,
                        action_id: str = None,
                        action_state: ActionState = None,
                        guild_id: str = None):
        """
        Find an Action in state management based on filter criteria.
        params:
            action_id: The unique identifier of a Action to filter the results with.
            action_state: The state of Actions to filter the results with.
            guild_id: The guild id of Actions to filter the results with.
        """
        state = self.persistence.get_state()
        state_enumerable = Enumerable(state['decisions'])
        logging.info(f'Finding actions with id: {action_id}, state: {action_state}, guild_id: {guild_id}')

        # If an id is provided, return the decision with that id
        if action_id:
            # use pylinq to find actions with the provided id
            action = state_enumerable.select_many(lambda x: x.actions).where(lambda x: x.id_ == action_id).first_or_default()
            logging.info(f'Found action: {action}')
            return action
                # TODO: Handle scenario where none are found of this id
        # If no id is provided, return all decisions with the provided state
        elif action_state:
            if guild_id:
                state_enumerable = state_enumerable.where(lambda x: x.guild_id == guild_id)
            state_enumerable = state_enumerable.select_many(lambda x: x.actions).where(lambda x: x.action_state == action_state)
            logging.info(f'Found actions: {state_enumerable}')
            logging.info(f'Found actions: {state_enumerable[0]}')
                # TODO: Handle scenario where none are found of this state
            return state_enumerable
        return None