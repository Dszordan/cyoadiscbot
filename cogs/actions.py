"""
    A Discord Cog that is a collection of commands related to managing Decisions.
"""
import logging

from discord import Emoji, PartialEmoji, Embed
from discord.ext import commands
from discord.ext.commands import Context

from file_persistence import file_persistence
from model.decision import Decision, DecisionState, Action, ActionState
from utils.display import DecisionDisplayEmbed, GenericDisplayEmbed

class Actions(commands.Cog):
    def __init__(self, bot, persistence: file_persistence):
        logging.basicConfig(level=logging.INFO)
        self.bot = bot
        self.persistence = persistence
        self.decisions = self.bot.get_cog('Decisions')
        self.user_interaction = self.bot.get_cog('UserInteraction')

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
        selected_decision = decision
        if not decision:
            selected_decision = await self.decisions.choose_decision(ctx, DecisionState.PREPARATION)
        
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
        
        await DecisionDisplayEmbed(selected_decision, channel, ctx).send_message()
        message_str = 'Does this look good? (y/n)\n'
        await GenericDisplayEmbed('Create Action', message_str, channel).send_message()
        response = await self.user_interaction.await_response(ctx, ['y', 'n'], timeout=30, channel=channel)
        if not response:
            return None
        if response == 'n':
            await ctx.author.send(f'Action creation cancelled.')
            return None

        new_action = Action(glyph=action_glyph, description=action_description, previous_decision=selected_decision)
        selected_decision.actions.append(new_action)
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
        
        new_action = Action(glyph=action_glyph, description=action_description, previous_decision=selected_decision, action_state=ActionState.PROPOSED)
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
        # publish_channel_name = self.persistence.get_admin_state()['channels']['publish']
        dm_channel_name = self.persistence.get_admin_state()['channels']['dm']
        # publish_channel = next((x for x in guild.channels if x.name == publish_channel_name), None)
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

        # Find the specific discord message object
        # message = await publish_channel.fetch_message(selected_decision.message_id)
        # updated_embed = DecisionDisplayEmbed(selected_decision, ctx.author, ctx)
        # await message.edit(embed=updated_embed.embed)
        # await message.add_reaction(new_action.glyph)

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
