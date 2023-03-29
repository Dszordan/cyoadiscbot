import asyncio
from discord.ext import commands
class UserInteraction(commands.Cog):
    def __init__(self,
                 bot: commands.Bot):
        self.bot = bot

    # Bot awaits for a response from the user.
    async def await_response(self, ctx, valid_options = [], timeout = 30, channel = None):
        # Ensure selection is within the bounds of choice
        def check(msg):
            context_channel = ctx.channel
            if channel:
                context_channel = channel
            return msg.channel == context_channel \
                and msg.author == ctx.author \
                and msg.content.lower() in valid_options

        response = ''
        try:
            if valid_options:
                response = await self.bot.wait_for("message", timeout=timeout, check=check)
            else:
                response = await self.bot.wait_for("message", timeout=timeout)
        except asyncio.TimeoutError:
            response = None

        # Display decision
        if response:
            if response.content == 'c':
                response = None
            else:
                return response.content
        if response is None:
            await ctx.send("Selection timed out or was canceled.")
        return None
