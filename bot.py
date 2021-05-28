# bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.admin import AdminTools
from cogs.decisions import Decisions
from cogs.error_handler import CommandErrorHandler
from file_persistence import file_persistence

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
state_management = file_persistence('newfile.yaml')

# client = discord.Client()
bot = commands.Bot(command_prefix='!')
bot.add_cog(AdminTools(bot))
bot.add_cog(Decisions(bot, state_management))
bot.add_cog(CommandErrorHandler(bot))

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to {guild}!')

@bot.command(name='rolldice', help='Roll a number of dice')
async def rolldice(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

bot.run(TOKEN)