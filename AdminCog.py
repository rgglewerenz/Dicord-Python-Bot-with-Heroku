"""
HEllO AND THANK YOU FOR USING MY APPLICATION
PLEASE READ THE DOCS BELOW FOR INFORMATION
ABOUT WHAT FEATURES THIS PROGRAM HAS
"""
from discord.ext import commands
import discord
class AdminCog(commands.Cog):
    """
    Functions:
    on_message = whenever a user sends a message it is checked to see what to do
    unmute = unmutes the user, or another user, depending on the given parameters
    mute = mutes the user, or another user, depending on the given parameters
    disconnect = disconnects the user, or another user, depending on the given parameters

    for any question on spesific features please read the docs for the given function.
    """
    def __init__(self, bot):
        self.bot = bot
        self.text_channel_list = []
        self.bad_words = ["add items to ban here"]
        self.all_emojies = {}
        self.guilds = {}
        self.roles = {}

    #some debug info so that we know the bot has started
    @commands.Cog.listener()
    async def on_ready(self):
        """
        Once the bot has started up it
        filles in the information within
        the init function.
        """
        for guild in self.bot.guilds:
            guild_emogjies = {}
            guild_roles_list = {}
            for emoji in guild.emojis:
                guild_emogjies.update({emoji.name:emoji})
            for role in guild.roles:
                guild_roles_list.update({role.name:role})
            self.roles.update({guild:guild_roles_list})
            self.all_emojies.update({guild:guild_emogjies})
            self.guilds.update({guild.name:guild})
        print("-----Everything is good to go-------")
    @commands.Cog.listener()
    async def on_message(self,message):
        """
        Whenever a user sends a message it
        is put through the filter to see
        what should be done to it:

        Bad words get deleted.

        gamer words get a reply from the bot
        with a message.

        cringe words get a message telling them
        that it is cringe, and then procedes to
        delete the message.

        funny words get a reply from the bot
        that mocks them for overusing
        these messages

        and any message not sent by a
        specified user gets upvoted
        while the specified user
        gets downvoted.
        """
        guilld = message.guild
        if message.author == self.bot.user:
            pass
        else:
            for i in self.bad_words:
                if i in message.content.lower():
                    await message.delete()
    @commands.command(name = "unmute")
    async def unmute(self,ctx, *args):
        """
        If no parameters are given
        then it will check to see if
        the user has the given permissions
        to unmute people, and will then unmute
        the sender.

        If a parameter is given, then it will
        try and find the user with a spesific
        key words in their name, and unmute them
        """
        guild_roles = self.roles[ctx.guild]
        user_roles = ctx.author.roles
        required_roles = ["Admin","Moderators","Owner","Co-Owner"]
        has_persm = False
        for roles in required_roles:
            if guild_roles[roles] in user_roles:
                name = "".join(args)
                guild = ctx.guild
                if name == "":
                    member = ctx.author
                    await member.edit(mute = False)
                for member in range(len(guild.members)):
                    if name in str(guild.members[member]):
                        member= guild.members[member]
                        await member.edit(mute = False)
                has_persm = True
        if has_persm is  False:
            embed = discord.Embed(
                            title= "Error",
                            color=0xFF5733,
                            type = 'rich',
                            description = "You do not have permission to use this command"
                        )
            await ctx.send(embed=embed)
    @commands.command(name = "mute")
    async def mute(self,ctx,*args):
        """
        If no parameters are given
        then it will check to see if
        the user has the given permissions
        to mute people, and will then unmute
        the sender.

        If a parameter is given, then it will
        try and find the user with a spesific
        key words in their name, and mute them
        """
        guild_roles = self.roles[ctx.guild]
        user_roles = ctx.author.roles
        required_roles = ["Admin","Moderators","Owner","Co-Owner"]
        has_persm = False
        for roles in required_roles:
            if guild_roles[roles] in user_roles:
                name = "".join(args)
                guild = ctx.guild
                if name == "":
                    member = ctx.author
                    await member.edit(mute = True)
                for member in range(len(guild.members)):
                    if name in str(guild.members[member]):
                        member= guild.members[member]
                        await member.edit(mute = True)
                has_persm = True
        if has_persm is  False:
            embed = discord.Embed(
                            title= "Error",
                            color=0xFF5733,
                            type = 'rich',
                            description = "You do not have permission to use this command"
                        )
            await ctx.send(embed=embed)
    @commands.command(name = "disconnect")
    async def disconnect(self,ctx, *args):
        """
        If no parameters are given
        then it will check to see if
        the user has the given permissions
        to disconnect people, and will then
        unmute the sender.

        If a parameter is given, then it will
        try and find the user with a spesific
        key words in their name, and
        disconnect them
        """
        guild_roles = self.roles[ctx.guild]
        user_roles = ctx.author.roles
        required_roles = ["Admin","Moderators","Owner","Co-Owner"]
        has_persm = False
        for roles in required_roles:
            if guild_roles[roles] in user_roles:
                name = "".join(args)
                guild = ctx.guild
                if name == "":
                    member = ctx.author
                    await member.move_to(None)
                for member in range(len(guild.members)):
                    if name in str(guild.members[member]):
                        member= guild.members[member]
                        await member.move_to(None)
                has_persm = True
        if has_persm is False:
            embed = discord.Embed(
                            title= "Error",
                            color=0xFF5733,
                            type = 'rich',
                            description = "You do not have permission to use this command"
                        )
            await ctx.send(embed=embed)
