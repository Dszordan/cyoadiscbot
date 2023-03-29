"""
    A Discord Cog that is a collection of commands related to managing Decisions.
"""
from discord import Emoji, PartialEmoji
from discord.ext import commands
from discord.ext.commands import Context

from file_persistence import file_persistence
from model.decision import Decision, DecisionState, Action
from utils.display import DecisionDisplayEmbed, GenericDisplayEmbed

class Actions(commands.Cog):
    def __init__(self, bot, persistence: file_persistence):
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
                await self.create_action(ctx, selected_decision)
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
        published_decisions = self.decisions.find_decisions(decision_state=DecisionState.PUBLISHED)
        selected_decision = None
        if not published_decisions:
            await ctx.author.send('Unfortunately there are no published decisions to propose an action to. Wait until a decision has been published first!')
            return
        if len(published_decisions) > 1:
            await ctx.author.send('There are multiple published decisions. Please select one of the following:')
            selected_decision = await self.decisions.choose_decision(ctx, state=DecisionState.PUBLISHED)
        else:
            selected_decision = published_decisions[0]
        await ctx.author.send(f'Hey there {ctx.author.name}, I\'m responding to your action proposal. Let\'s create a new action. What is the description of the action?')
        new_action = await self.create_action(ctx.author, decision=selected_decision, channel=ctx.author)
        if new_action:
            # need republish or update them embed AND add an action to the decision
            print("TODO: implement action proposal")

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
            print('could not find that action to update.')
