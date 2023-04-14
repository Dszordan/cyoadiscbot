import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context

from utils.display import GenericDisplayEmbed

class AdminTools(Cog):

    def __init__(self, bot, state_management):
        self.bot = bot
        self.state_management = state_management
        self.user_interaction = self.bot.get_cog('UserInteraction')

    @commands.command(name='SetDMChannel')
    async def set_dm_channel(self,
                             ctx: Context,
                             channel: discord.TextChannel):
        admin_state = self.state_management.get_admin_state()
        previous_channel = admin_state["channels"]["dm"]
        print(f'Set DM channel from {previous_channel} to {channel}.')
        admin_state['channels']['dm'] = channel.name
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'DM Channel updated to {channel}')

    @commands.command(name='SetPublishChannel')
    async def set_publish_channel(self,
                                  ctx: Context,
                                  channel: discord.TextChannel):
        admin_state = self.state_management.get_admin_state()
        previous_channel = admin_state["channels"]["publish"]
        print(f'Set DM channel from {previous_channel} to {channel}.')
        admin_state['channels']['publish'] = channel.name
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'Publish Channel updated to {channel}')
    
    @commands.command(name='setcampaigndescription')
    async def set_campaign_description(self,
                                   ctx: Context):
        admin_state = self.state_management.get_admin_state()
        campaign_definition = admin_state["campaign_definition"]
        previous_description = campaign_definition["description"]
        previous_name = campaign_definition["title"]
        previous_theme = campaign_definition["theme"]
        
        if previous_name is None:
            await GenericDisplayEmbed('campaign Title', "Title your campaign.", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            campaign_definition['title'] = response
        else:
            await GenericDisplayEmbed('Modify Existing campaign Title', f"Title your campaign. Your current title is {campaign_definition['title']}", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            if response:
                campaign_definition['title'] = response
        
        if previous_description is None:
            await GenericDisplayEmbed('campaign Description', "Describe your campaign.", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            campaign_definition['description'] = response
        else:
            await GenericDisplayEmbed('Modify Existing campaign Description', f"Describe your campaign. Your current description is {campaign_definition['description']}", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            if response:
                campaign_definition['description'] = response
        
        if previous_theme is None:
            await GenericDisplayEmbed('campaign Theme', "Theme your campaign. (Comma separated themes. [horror, fantasy])", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            campaign_definition['theme'] = response
        else:
            await GenericDisplayEmbed('Modify Existing campaign Theme', f"Theme your campaign. Your current theme is {', '.join(campaign_definition['theme'])}", ctx.channel).send_message()
            response = await self.user_interaction.await_response(ctx)
            if response:
                # split the response into a list, remove any whitespace
                theme_list = response.split(',')
                stripped_list = [theme.strip() for theme in theme_list]
                # print the list in a single line
                print(', '.join(stripped_list))
                campaign_definition['theme'] = stripped_list

        admin_state["campaign_definition"] = campaign_definition
        self.state_management.write_admin_state(admin_state)
        await ctx.send(f'campaign Description updated to {admin_state}')

    @commands.command(name='displaycampaigndescription')
    async def display_campaign_description(self,
                                        ctx: Context):
        admin_state = self.state_management.get_admin_state()
        publish_channel = admin_state['channels']['publish']
        channel = next((x for x in ctx.guild.channels if x.name == publish_channel), None)
        print(ctx.guild.channels)
        print(channel)
        campaign_definition = admin_state["campaign_definition"]
        title = campaign_definition["title"]
        description = campaign_definition["description"]
        theme = campaign_definition["theme"]
        msg = f'{description}\n\n\nCampaign Theme: {", ".join(theme)}'
        await GenericDisplayEmbed(title, description, channel).send_message()

    def get_dm_channel(self, guild_id):
        dm_state = self.state_management.get_admin_state()
        dm_channel = dm_state['channels']['dm']
        guild = self.bot.get_guild(guild_id)
        return next((x for x in guild_id.channels if x.name == dm_channel), None)

    def get_publish_channel(self, guild_id):
        admin_state = self.state_management.get_admin_state()
        publish_channel = admin_state['channels']['publish']
        return next((x for x in guild_id.channels if x.name == publish_channel), None)
    
    def get_notifications_channel(self, guild_id):
        admin_state = self.state_management.get_admin_state()
        notifications_channel = admin_state['channels']['notifications']
        return next((x for x in guild_id.channels if x.name == notifications_channel), None)
