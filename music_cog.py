import discord
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands.core import guild_only
from spotipy.exceptions import SpotifyException
from youtube_dl import YoutubeDL
import spotipy
from spotipy import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyClientCredentials

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #all the music related stuff
        self.is_playing = False
        client_credentials_manager = SpotifyClientCredentials(client_id='Spotify Id',
                                                              client_secret='Spotify secrets')
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.voice_channel = "" #This will be assigned to whatever voice Channel that the user is in
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
                                'options': '-vn'}
        self.titleplaying = "" #This will be assigned to whatever song is currently playing 
        self.titlequeued = "" #This will be assigned to whatever song was just added to queue
        self.players = {} #Creates a dictionary with the Server and with the Voice Client 
        self.music_queue={} #Creates a dictionary with the key being the server Id and the item being the queue list

    #searching the item on youtubeF
    def search_yt(self, item):
        with YoutubeDL( self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}
    #Automatically queues up the next song
    def play_next(self, guild):
        if len(self.music_queue[guild])>0:
            self.is_playing = True
            guildqueue=  self.music_queue[guild] #turns the dict into a list for the spesific guild
            nextsong = guildqueue[0]
            nextsong =  self.search_yt(nextsong) #Looks up the name of the track on YT
            nextsong = nextsong['source']
            self.music_queue[guild].pop(0) #Removes the the song from the queue as it is added to the player
            self.players[guild].play(discord.FFmpegPCMAudio(nextsong, 
                                     ** self.FFMPEG_OPTIONS),
                                     after=lambda e: self.play_next(guild)   #After it is done playing the song it exicutes the play_next command
                                    )
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self, guild):
        if len(self.music_queue[guild]) > 0:
            print(self.music_queue)
            guildqueue=  self.music_queue[guild] #turns the dict into a list for the spesific guild
            nextsong = guildqueue[0]
            nextsong =  self.search_yt(nextsong) #Looks up the name of the track on YT
            nextsong = nextsong['source']
            self.music_queue[guild].pop(0) #Removes the the song from the queue as it is added to the player
            self.is_playing = True
            self.players[guild].play(discord.FFmpegPCMAudio(nextsong, 
                        **self.FFMPEG_OPTIONS), 
                        after=lambda e: self.play_next(guild) #After it is done playing the song it exicutes the play_next command
                        )
        else:
            self.is_playing = False
        
    #Play command 
    @commands.command(aliases = ['-p','play'], help="Plays a selected song from youtube")
    async def p(self, ctx, *args):
        guild = ctx.guild
        query = " ".join(args)
        self.voice_channel = ctx.author.voice.channel
        guildqueue = [] 
        if self.voice_channel is None: #Checks if the user is connected to a voice channel 
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Please connect to a voice channel"
                                )
            await ctx.send(embed = embed)
        else:
            #checks to see if the user inputed a song or a playlist
            try:
                if 'open.spotify.com' in query:
                    author= self.spotify.track(query)
                    artists =author['artists']
                    test = artists[0]
                    name = test['name']
                    query = name + author['name']
                    self.music_queue.update({guild :guildqueue.append(query)})
            except SpotifyException:
                if 'open.spotify.com' in query:
                    author= self.spotify.playlist(query)
                    tracks = author['tracks']
                    items = tracks['items']
                    x=0
                    for i in items: #For every item in the playlist it will get the name of the artist and the name of the track in order to add it to the queue
                        artists = items[x]
                        track = artists['track']
                        artist = track['artists']
                        whichone = artist[0]
                        #gets the 1st artist listed 
                        author = whichone['name']
                        name = track['name']
                        query = name + ' '+  author #Adds the name of the autor to the track name in ordert to 
                        try: #Tries to see if a music queue already exists in this server
                            guildqueue = self.music_queue[guild] 
                            if type(guildqueue) != list:
                                guildqueue = []
                        except KeyError: # If no queue already exits then it makes the queue and adds the aporpriate songs to the queue 
                            self.music_queue.update({guild:[]})
                        guildqueue = self.music_queue[guild]
                        guildqueue.append(query)
                        self.music_queue.update({guild:guildqueue})
                        print(self.music_queue)
                        x = x +1 
                    await self.j(ctx) # Makes the bot join the discord channel 
                    await self.play_music(guild) #Makes the bot play the items in queue
                    embed=discord.Embed( 
                                            title= "Spotify", 
                                            color=0xFF5733,
                                            type = 'rich',
                                            description = "Added all items to the queue"
                                        )
                    await ctx.send(embed = embed)
                    return ctx
            song =  self.search_yt(query)
            if type(song) == type(True): #Checks to see if the desired link or keyword is an availiable video for the bot to play
                embed=discord.Embed( 
                                        title= "Error", 
                                        color=0xFF5733,
                                        type = 'rich',
                                        description = "Could not download the song. Please make sure that it is not a playlist or livestream"
                                    )
                await ctx.send(embed = embed)
            else:
                #adds inputed song to the bot
                try:
                    guildqueue = self.music_queue[guild] #Checks to see if a queue within this server already exists
                except KeyError:
                    self.music_queue.update({guild:[]})
                guildqueue = self.music_queue[guild]
                guildqueue.append(song['title'])
                self.music_queue.update({guild:guildqueue})
                print(self.music_queue)
                self.titlequeued =  song['title']
                if self.is_playing == True:
                    message =  self.titlequeued + " is added to the queue"
                    embed=discord.Embed( 
                                    title= "Queue", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = message
                                    )
                    await ctx.send(embed = embed)
                embed=discord.Embed( 
                                    title= self.titlequeued +" has been added to queue", 
                                    color=0xFF5733,
                                    type = 'rich'
                                    )
                if  self.is_playing == False:
                    try:
                        await self.j(ctx)
                        await self.play_music(guild)
                        await ctx.send(embed = embed)
                    except ClientException:
                        await self.play_music(guild)
                        await ctx.send(embed = embed)
            try:         
                if  self.players[guild] == self.voice_channel:
                    print("in same vc")
            except:
                await self.j(ctx)
                await self.play_music(guild)
            else:
                await self.players[guild].move_to(self.voice_channel)

    @commands.command(aliases = ['-q','queue'], help="Displays the current songs in queue")
    async def q(self, ctx):
        guild = ctx.guild
        try:
            guildqueue =self.music_queue[guild] 
        except KeyError:
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is no queue in this server"
                                    )
            await ctx.send(embed =embed)
        retval = ""
        if  guildqueue != []:
            if len( self.music_queue)>0:
                for i in range(len(self.music_queue[guild])):
                    retval = retval + (str(i+1) + ': ' + guildqueue[i] + "\n")
                embed=discord.Embed(
                                    title="Queue", 
                                    description=retval, 
                                    color=0xFF5733)
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(
                                    title="Queue", 
                                    description="There are no items currently in the queue", 
                                    color=0xFF5733)
                await ctx.send(embed=embed)

    #Skip command
    @commands.command(aliases = ['s', '-skip','next','n'], help="Skips the current song being played")
    async def skip(self, ctx):
        guild = ctx.guild
        if  self.players[guild] != "" and  self.players[guild]:
            self.players[guild].stop()
            #try to play next in the queue if it exists
            await  self.play_music()
    
    #Move command
    @commands.command(aliases = ['move'],help = "Changes the queue placement")
    async def m(self, ctx, From, TO):
        to = int(TO)
        fromvar = int(From)
        guild = ctx.guild
        try:
            guildqueue = self.music_queue[guild]
        except ValueError:
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is no queue for this server"
                                    )
            await ctx.send(embed = embed)                    
        print(guildqueue)
        if to < len(guildqueue)+1:
            tempvarto = (guildqueue[to-1])
            tempvarfrom = (guildqueue[fromvar-1])
            print(tempvarto)
            if to > fromvar: 
                 guildqueue.insert(fromvar,tempvarto)
                 guildqueue.insert(to, tempvarfrom)
                 guildqueue.pop(to+1)
                 guildqueue.pop(fromvar-1)
            if fromvar > to:
                 guildqueue.insert(fromvar,tempvarto)
                 guildqueue.insert(to, tempvarfrom)
                 guildqueue.pop(to-1)
                 guildqueue.pop(fromvar+1)
            print(self.music_queue)
            self.music_queue.update({guild:guildqueue})
            guildqueue = []
        else:
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Please enter a number that is small than the queue size"
                                    )
            await ctx.send(embed = embed)

    @commands.command(aliases = ['clear', 'r', 'remove'], help = "Removes all songs the the current queue")
    async def c(self, ctx, *args):
        query = "".join(args)
        voice_channel = ctx.author.voice.channel
        guild = ctx.guild
        try:
            guildqueue = self.music_queue[guild]
        except IndexError:
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "No queue in this server has been made"
                                    )
            await ctx.send(embed = embed)
        if voice_channel is None:
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Please connect to a vc"
                                    )
            #you need to be connected so that the bot knows where to go
            await ctx.send(embed = embed)
        else:
            #Checks to see if the query is filled out
            if query == "":
                for i in range(0, len(guildqueue)):
                    guildqueue.pop(0) # If so then it will remove all items in the queue
                embed=discord.Embed( 
                                    title= "Queue", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "All music has been purged from the queue"
                                    )
                await ctx.send(embed = embed)
                self.players[guild].stop()
                self.is_playing = False
                self.music_queue.update({guild:guildqueue})
            else: #if query is filled out then it will try and see of any items in the list fits the description of the item
                for song in range(len( self.music_queue)+1):
                    if query in  self.music_queue:
                        message = "You have sucsessfully removed " +  guildqueue[song] + " from the queue"
                        embed=discord.Embed( 
                                    title= "Queue", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = message
                                    )
                        await ctx.send(embed = embed)
                        guildqueue.pop(song)
                    else: #if no items exist that contain query in the name then it will ouput an error message
                        embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Please enter a number that is within the desired track"
                                    )
                        await ctx.send(embed =embed)
                self.music_queue.update({guild:guildqueue})
                        

    @commands.command(aliases = ['l'], help = "Makes the bot leave the vc")
    async def leave(self, ctx):
        guild =ctx.guild 
        if (self.players[guild].is_connected()): # If the bot is in a voice channel 
            await  self.players[guild].disconnect() # Leave the channel
            embed=discord.Embed( 
                                    title= "Bot", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Bot left"
                                    )
            await ctx.send(embed = embed)
        else: # But if it isn't
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "I'm not currently in a voice channel use the join command to make me join"
                                    )
            await ctx.send(embed =embed)
    #Join command
    @commands.command(aliases = ['join'], help = "Makes the bot join")
    async def j(self, ctx):
        guild = ctx.guild
        if (ctx.author.voice): # If the person is in a channel
            channel = ctx.author.voice.channel
            try: # Checks to see if there is a player within that guild
                self.players[guild]
            except KeyError: #If not it will make the bot 
                vc = await channel.connect()
                self.players.update({guild:vc})

            if self.players == {}: #If there are no players currently
                vc = await channel.connect()
                self.players.update({guild:vc})
            if ctx.author.voice.channel != self.players[guild]: #If the user is in a different channel from what the bot is in it will move the bot to their vc 
                self.players[guild].move_to(channel)
            else: # If none of the condtions above are filled out then it will make a new voice voice client in the channel from which the message was sent
                vc=await channel.connect()
                self.players.update({guild: vc})
                print(self.players)
        else: #But if the users isnt connect to a voice channel then it will output this error message
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "You must be in a voice channel for me to join it"
                                    )
            await ctx.send(embed = embed)
        print(self.players)
    #pause command
    @commands.command(aliases = ['stop'] , help = "Makes the bot pause")
    async def pause(self, ctx):
        guild = ctx.guild
        if  self.music_queue == "":
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is nothing that is -currently playing"
                                    )
            await ctx.send(embed = embed)
        else:
            self.players[guild].pause()
    #resume command
    @commands.command(name = 'resume', help = "Makes the bot resume playing")
    async def resume(self, ctx):
        guild = ctx.guild
        if  self.music_queue == "":
            embed=discord.Embed( 
                                    title= "Error", 
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is nothing playing now"
                                    )
            await ctx.send(embed = embed)
        else:
            self.players[guild].resume()