import discord
from discord.ext import commands
from discord.ext.commands import Cog, Bot

class AdminTools(Cog):

    def __init__(self, bot, state_management):
        self.bot = bot
        self.state_management = state_management
    
    @commands.command(name='changedefaultproperty')
    async def change_default_properties(self, ctx, property_name: str, property_value):
        print(f'change property: {property_name} to {property_value}')

    @commands.command(name='SetDMChannel')
    async def set_dm_channel(self, ctx, channel: discord.TextChannel):
        admin_state = self.state_management.get_admin_state()
        admin_state['channels']['admin'] = channel
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'DM Channel updated to {channel}')