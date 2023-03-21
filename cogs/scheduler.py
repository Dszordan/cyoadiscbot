import logging

import discord
from discord.ext import commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class Scheduler(commands.Cog):
    """Schedule commands."""
    def __init__(self, bot):
        self.bot = bot

        # Initialize session
        # self.session = aiohttp.ClientSession()
        self.schedule()
    
    # Scheduled events
    async def schedule_func(self):
        print('schedule')

    def schedule(self):
        # Initialize scheduler
        schedule_log = logging.getLogger("apscheduler")
        schedule_log.setLevel(logging.WARNING)

        job_defaults = {
            "coalesce": True,
            "max_instances": 5,
            "misfire_grace_time": 15,
            "replace_existing": True,
        }

        scheduler = AsyncIOScheduler(job_defaults = job_defaults, 
                          logger = schedule_log)

        # Add jobs to scheduler
        scheduler.add_job(self.schedule_func, CronTrigger.from_crontab("*/1 * * * *")) 
