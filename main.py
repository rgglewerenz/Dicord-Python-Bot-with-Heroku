__doc__ = "This is the main file that is used to run the application"
import  discord
from discord.ext import commands
from AdminCog import AdminCog
from ImageCog import ImageCog
from MusicCog import MusicCog
from main_cog import main_cog


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix= '!', intents = intents)
bot.add_cog(main_cog(bot))
bot.add_cog(MusicCog(bot))
bot.add_cog(AdminCog(bot))
bot.add_cog(ImageCog(bot))

#Initializer
bot.run('Discord Bot Token')
