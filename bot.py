# bot.py
import os
import random
import discord
from discord.ext.commands import context
import emoji
import regex
from discord import Embed, Colour
from typing import Union
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

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
async def prepare_decision(ctx, body: str, *decisions: Union[discord.Emoji, discord.PartialEmoji, str]):
    actions = []
    body+='\n'
    for decision in decisions:
        print(decision)
        emoji = decision.split('|')[0]
        description = decision.split('|')[1]
        actions.append({
            'glyph': emoji,
            'description': description
        })
        body+=emoji + ' = ' + description + '\n' 
    emb = Embed(
        description=body,
        colour=discord.Colour.blue()
        ).set_thumbnail(url='https://www.dndbeyond.com/avatars/13704/589/1581111423-38596430.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp'
        ).set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
    decision_body = await ctx.channel.send(
        content=body,
        embed=emb)
    for action in actions:
        print(action['glyph'] + ' ' + action['description'])
        await decision_body.add_reaction(action['glyph'])

# def create_actions(emojis):


def split_count(text):
    emoji_list = []
    data = regex.findall(r'\X', text)
    for word in data:
        if any(char in emoji.UNICODE_EMOJI for char in word):
            emoji_list.append(word)

    return emoji_list

# @client.event
# async def on_message(message):
#     if message.author.name != client.user.name:
#         print(message.content)
#         if str(message.content).find('xyz') != -1:
#             print('message contains xyz')
#             try:
#                 await message.author.create_dm()
#             except:
#                 pass
#             await message.author.dm_channel.send(f'Greetings, thanks for the message: {message.content}')

# @client.event
# async def on_error(event, *args, **kwargs):
#     with open('err.log', 'a') as f:
#         if event == 'on_message':
#             f.write(f'Unhandled message: {args[0]}\n')
#         else:
#             raise()

# client.run(TOKEN)
bot.run(TOKEN)