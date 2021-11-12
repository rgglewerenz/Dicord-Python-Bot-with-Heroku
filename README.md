# Dicord-Python-Bot-with-Heroku
This is a bot that will use the Heroku cloud computing service to run the bot 24/7
All you need to do is create a discord bot and a spotify devolper profile, and the replace  line 16 and 17 in the music cog with their respective Id and Secret keys
You will also need to get the DIscord Bot token, and replace line 14 in main.py
Then just make a Heroku accound and add these urls to the buildpacks:
https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
https://github.com/xrisk/heroku-opus.git
heroku/python
