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
                             decision: Decision = None):
        """
        Create an action for a decision.
        params:
            ctx: The Discord context in which the command has been executed within.
            decision: The decision to modify actions for. If not provided, the user will be prompted to select one.
        """
        selected_decision = decision
        if not decision:
            selected_decision = await self.decisions.choose_decision(ctx, DecisionState.PREPARATION)
        
        message_str = 'Describe the action. (c to cancel)\n'
        await GenericDisplayEmbed('Create Action', message_str, ctx.channel).send_message()
        action_description = await self.user_interaction.await_response(ctx)
        
        message_str = 'Give the action a glyph/emoji (c to cancel)\n'
        await GenericDisplayEmbed('Create Action', message_str, ctx.channel).send_message()
        action_glyph = await self.user_interaction.await_response(ctx)

        selected_decision.actions.append(Action(glyph=action_glyph, description=action_description, previous_decision=selected_decision))
        await self.decisions.update_decision(selected_decision)

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
        
        # TODO: fix this
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
