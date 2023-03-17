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
        previous_channel = admin_state["channels"]["dm"]
        print(f'Set DM channel from {previous_channel} to {channel}.')
        admin_state['channels']['dm'] = channel.name
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'DM Channel updated to {channel}')

    @commands.command(name='SetPublishChannel')
    async def set_publish_channel(self, ctx, channel: discord.TextChannel):
        admin_state = self.state_management.get_admin_state()
        previous_channel = admin_state["channels"]["publish"]
        print(f'Set DM channel from {previous_channel} to {channel}.')
        admin_state['channels']['publish'] = channel.name
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'Publish Channel updated to {channel}')
