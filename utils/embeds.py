import random

import discord

class DefaultEmbed(discord.Embed):
    
    def __init__(self, **kwargs):
        super(DefaultEmbed, self).__init__(**kwargs)
        self.colour = random.randint(0, 0xffffff)
    
class CharacterEmbed(discord.Embed):

    def __init__(
            self,
            ctx,
            player = None,
            title = None,
            description = None,
            body = None,
            **kwargs
        ):
        super(CharacterEmbed, self).__init__(**kwargs)
        self.player = player
        self.set_thumbnail(url=self.generate_thumbnail_url())
        self.set_author(name=ctx.author.name,icon_url=ctx.author.avatar)
        self.colour = random.randint(0, 0xffffff)
        if title:
            self.title = title
        if description:
            self.description = description
        if body:
            self.body = body

    def generate_thumbnail_url(self):
        """
            Generate a thumbnail URL of a player using their DND player sheet
            # TODO: Figure out a way to generate this
            params:
                player = the player to get the thumbnail of
        """
        url = self.player # Remove this
        url = 'https://www.dndbeyond.com/avatars/13704/589/1581111423-38596430.jpeg'
        url += '?width=150&height=150&fit=crop&quality=95&auto=webp'
        return url