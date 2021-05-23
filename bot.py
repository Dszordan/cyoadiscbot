# bot.py
import os
import random
import discord
from discord import message
from discord.ext.commands import context
from discord.ext.commands.core import check
import emoji
import regex
from model import decision, decision_state
from file_persistence import file_persistence
from discord import Embed, Colour
from typing import Union
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
state_management = file_persistence('newfile.yaml')

# client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to {guild}!')

@bot.command(name='respond', help='responds to a user')
async def respond(ctx):
    await ctx.send('hi there')

@bot.command(name='rolldice', help='Roll a number of dice')
async def rolldice(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

@bot.command(name='preparedecision')
async def prepare_decision(ctx, body: str, *actions: Union[discord.Emoji, discord.PartialEmoji, str]):
    parsed_actions = []
    rich_body = body + '\n'
    for action in actions:
        print(action)
        emoji = action.split('|')[0]
        description = action.split('|')[1]
        parsed_actions.append({
            'glyph': emoji,
            'description': description
        })
        rich_body+=emoji + ' = ' + description + '\n'
    # create decision model
    d = decision(1, body, parsed_actions)
    state_management.write_state([d])
    emb = Embed(
        description=rich_body,
        colour=discord.Colour.blue()
        ).set_thumbnail(url='https://www.dndbeyond.com/avatars/13704/589/1581111423-38596430.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp'
        ).set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
    decision_message = await ctx.channel.send(
        content=rich_body,
        embed=emb)
    for action in parsed_actions:
        print(action['glyph'] + ' ' + action['description'])
        await decision_message.add_reaction(action['glyph'])

@bot.command(name='viewdecisions')
async def view_decisions(ctx, decision_state: str = decision_state.PREPARATION):
    state = state_management.get_state()
    choices = []
    message_str = 'Found decision(s), which one do you want to view:'
    for decision in state:
        choices.append(decision)
        message_str += f'\n [{len(choices)}] {str(decision.body)[0:20]}'
    def check(m):
        return int(m.content) in [1,2,3,4] and m.channel == ctx.channel
    await ctx.send(message_str)
    msg = await bot.wait_for("message", check=check)
    display_decision = choices[int(msg.content) - 1]
    await ctx.send(f"Viewing {display_decision.id}, {display_decision.body} ")

def split_count(text):
    emoji_list = []
    data = regex.findall(r'\X', text)
    for word in data:
        if any(char in emoji.UNICODE_EMOJI for char in word):
            emoji_list.append(word)

    return emoji_list

# @bot.event
# async def on_message(message):
#     if message.author.name != bot.user.name:
        

# @client.event
# async def on_error(event, *args, **kwargs):
#     with open('err.log', 'a') as f:
#         if event == 'on_message':
#             f.write(f'Unhandled message: {args[0]}\n')
#         else:
#             raise()

# client.run(TOKEN)
bot.run(TOKEN)