from discord.ext import tasks, commands

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=5.0)
    async def printer(self):
        # call the decisions cog check_time method
        await self.bot.get_cog('Decisions').check_time()

    @commands.Cog.listener()
    async def on_ready(self):
        self.printer.start()
