from discord.ext import commands
from discord.ext.commands import Cog, Bot

class AdminTools(Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='changedefaultproperty')
    async def change_default_properties(self, ctx, property_name: str, property_value):
        print(f'change property: {property_name} to {property_value}')