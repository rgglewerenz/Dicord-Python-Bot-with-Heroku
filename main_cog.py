from os import supports_bytes_environ
import discord
from discord.ext import commands

class main_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.text_channel_lists = {}
        self.all_emojies = {}
        self.guilds = {}
        self.roles = {}

    #some debug info so that we know the bot has started
    """@commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            name = "raz"
            guild_text_list = {}
            guild_roles_list = {}
            for channel in guild.text_channels:
                guild_text_list.update({channel.name:channel})
            self.text_channel_lists.update({guild.name:guild_text_list})
            for role in guild.roles:
                guild_roles_list.update({role.name:role})
            self.roles.update({guild:guild_roles_list})
        print("ready")
        print(self.text_channel_lists)
        print(self.roles)"""