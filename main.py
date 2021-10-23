from discord.ext import commands
from music_cog import music_cog 
"""from main_cog import main_cog"""

bot = commands.Bot(command_prefix= '!')



"""bot.add_cog(main_cog(bot))"""
bot.add_cog(music_cog(bot))


#Initializer
bot.run('Discord bot token')
