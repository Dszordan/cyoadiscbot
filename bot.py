# bot.py
import logging
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# from cogs.admin import AdminTools
# from cogs.decisions import Decisions
# from cogs.error_handler import CommandErrorHandler
# from file_persistence import file_persistence

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
# state_management = file_persistence('testfile.yaml')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

# bot.add_cog(AdminTools(bot))
# bot.add_cog(Decisions(bot, state_management))
# bot.add_cog(CommandErrorHandler(bot))
MY_GUILD = discord.Object()
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to {guild}!')
    await bot.tree.sync(guild=GUILD)

@bot.tree.command()
async def test(interaction: discord.Interaction):
    await interaction.response.send('test')

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

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)