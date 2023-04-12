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

@bot.check
async def dm_channel_commands(ctx):
    # get admin state
    admin_state = state_management.get_admin_state()
    # if ctx channel name is not admin channel, disallow command
    if admin_state:
        if admin_state['channels']['dm']:
            if ctx.channel.name != admin_state['channels']['dm']:
                await ctx.send('This command is not allowed in this channel.')
                return False
    return True

async def main():
    await bot.add_cog(UserInteraction(bot))
    await bot.add_cog(Decisions(bot, state_management))
    await bot.add_cog(Actions(bot, state_management))
    await bot.add_cog(AdminTools(bot, state_management))
    await bot.add_cog(CommandErrorHandler(bot))
    await bot.add_cog(Scheduler(bot))

asyncio.run(main())
bot.run(TOKEN, log_handler=handler, log_level=logging.INFO)