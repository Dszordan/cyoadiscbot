import random

import discord

class DefaultEmbed(discord.Embed):
    
    def __init__(self, ctx, **kwargs):
        super(DefaultEmbed, self).__init__(**kwargs)
        self.colour = random.randint(0, 0xffffff)
    
class CharacterEmbed(discord.Embed):
    
    def __init__(self, ctx, title = None, description = None, body = None, **kwargs):
        super(CharacterEmbed, self).__init__(**kwargs)
        self.set_thumbnail(url='https://www.dndbeyond.com/avatars/13704/589/1581111423-38596430.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp')
        self.set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
        self.colour = random.randint(0, 0xffffff)
        if title:
            self.title = title
        if description:
            self.description = description
        if body:
            self.body = body
