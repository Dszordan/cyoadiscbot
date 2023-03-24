# bot.py
import asyncio
import logging
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.actions import Actions
from cogs.admin import AdminTools
from cogs.decisions import Decisions
from cogs.error_handler import CommandErrorHandler
from cogs.scheduler import Scheduler
from cogs.user_interaction import UserInteraction
from file_persistence import file_persistence

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
state_management = file_persistence()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

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

@rolldice.error
async def rolldice_error(ctx, error):
    await ctx.send(f'Sorry, I couldn\'t roll dice for you. Error: {error}')

async def main():
    await bot.add_cog(UserInteraction(bot))
    await bot.add_cog(Decisions(bot, state_management))
    await bot.add_cog(Actions(bot, state_management))
    await bot.add_cog(AdminTools(bot, state_management))
    await bot.add_cog(CommandErrorHandler(bot))
    await bot.add_cog(Scheduler(bot))

asyncio.run(main())
bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)