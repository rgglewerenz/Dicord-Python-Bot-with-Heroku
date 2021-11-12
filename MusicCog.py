"""
HEllO AND THANK YOU FOR USING MY APPLICATION
PLEASE READ THE DOCS BELOW FOR INFORMATION
ABOUT WHAT FEATURES THIS PROGRAM HAS
"""
import random
import discord
from discord.errors import ClientException
from discord.ext import commands
from spotipy.exceptions import SpotifyException
from youtube_dl import YoutubeDL
import spotipy
from spotipy import SpotifyClientCredentials
import pytube
class MusicCog(commands.Cog):
    """
    Functions:
    search_yt = looks up the desired input on youtube
    play_next = plays the next song in the queue
    play_music = initializes the bot to start playing the 1st song
    play = function that is triggered by a user input to create a queue and play music
    queue = sends an embed in the channel where called to display queue
    skip = skips the song currently playing
    move = changes the placement of an item in the queue with another player
    clear = removes either 1 item, or all items in a queue
    leave = makes the bot leave the vc
    join = makes the bot join the vc, or moves to the vc that the user is in
    pause = pauses the music player
    resume = resumes a paused bot
    play_file = is used to play discord spesific links
    search = gets a list of 10 items from a search query in yt, the user can add to queue
    """
    def __init__(self, bot):
        """
        Funtion that initializes the bot and creates global vars
        """
        self.bot = bot
        #all the music related stuff
        self.is_playing = False
        client_credentials_manager = SpotifyClientCredentials(
            client_id='Your spotify Id',
            client_secret='Your spotify Secret'
            )
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.voice_channel = "" #This will be assigned to whatever voice Channel that the user is in
        self.ytdl_options = {'format': 'bestaudio' , 'ignoreerrors' : True}
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'}
        self.queued_title = "" #This will be assigned to whatever song was just added to queue
        self.players = {} #Creates a dictionary with the Server and with the Voice Client
        self.music_queue={} #Makes each music queue tied to a spesific guild
        self.embed = ""
        self.playing = {}
        self.times_skipped = 0
    #searching the item on youtubeF
    def search_yt(self, item):
        """
        This function searches an item up on youtube and returns a dict with these keys:
        source = google link to play song
        title = gets the author of the yt video
        duration = gets the length of the yt video
        url = gets the url of the video
        """
        with YoutubeDL(self.ytdl_options) as ydl:
            if "youtube.com" in item:
                try:
                    info = ydl.extract_info(item, download=False )
                except Exception:
                    return False
            else:
                try:
                    info = ydl.extract_info("ytsearch:%s" % item, download=False )['entries'][0]
                except Exception:
                    return False
        return {'source': info['formats'][0]['url'],
                'title': info['title'],
                'image' : info['thumbnails'][3]['url'],
                'duration': info['duration'],
                'url': info['webpage_url']}
    #Automatically queues up the next song
    def play_next(self, ctx):
        """
        This will take the 1st item
        in the queue, and playes it.

        After it is done playing it will
        try to play the next item.

        If there are no tiems in the queue
        it will set is_playing to False
        """
        guild =ctx.guild
        if len(self.music_queue[guild])>0:
            self.is_playing = True
            guildqueue=  self.music_queue[guild] #turns the dict into a list for the spesific guild
            nextsong = guildqueue[0]
            if "https" in nextsong and "youtube" not in nextsong:
                #Removes the the song from the queue as it is added to the player
                self.music_queue[guild].pop(0)
                self.players[guild].play(
                discord.FFmpegPCMAudio(nextsong,
                        **self.ffmpeg_options),
                        after=lambda e: self.play_next(ctx)
                        #After it is done playing the song it exicutes the play_next command
                        )
            else:
                nextsong =  self.search_yt(nextsong) #Looks up the name of the track on YT
                if nextsong is False:
                    print("The song that the user has entered is not operational")
                else:
                    self.music_queue[guild].pop(0)
                    self.playing.update({guild: nextsong})
                    nextsong = nextsong['source']
                    self.is_playing = True
                    if self.players[guild].is_playing() is True:
                        self.players[guild].stop()
                    else:
                        self.players[guild].play(discord.FFmpegPCMAudio(nextsong,
                        **self.ffmpeg_options),
                        after=lambda e: self.play_next(ctx)
                        #After it is done playing the song it exicutes the play_next command
                        )
        else:
            self.is_playing = False
    # infinite loop checking
    async def play_music(self, ctx):
        """
        Makes the voice client play the
        1st item in the queue, and will
        delete it from the queue.
        """
        guild =ctx.guild
        if len(self.music_queue[guild])> 0:
            self.is_playing = True
            play =self.music_queue[guild][0]
            if "https" in play and "youtube" not in play:
                self.music_queue[guild].pop(0)
                self.players[guild].play(discord.FFmpegPCMAudio(play,
                **self.ffmpeg_options),
                after=lambda e: self.play_next(ctx))
            else:
                song =self.search_yt(play)
                if song is False:
                    await ctx.send("An error has occured")
                    self.music_queue[guild].pop(0)
                play = song['source']
                self.playing.update({guild:song})
                self.music_queue[guild].pop(0)
                self.players[guild].play(
                    discord.FFmpegPCMAudio(play,
                    **self.ffmpeg_options),
                    after=lambda e: self.play_next(ctx))
        else:
            self.is_playing = False
    #Play command
    @commands.command(aliases = ['-p','p', "P", "PLAY", "Play"],
        help="Plays a selected song from youtube; another name is play")
    async def play(self, ctx, *args):
        """
        This function with 1st check
        to see if the user has inputed a
        youtube link, spotify link,
        and a normal search term.

        If the user enters a search term,
        or a link it will then look up the item
        on youtube, and add it to queue.

        If the user enters a spotify track link
        or playlist link, it will get the
        name/names of the track/tracks

        Finally, it will check to see if the
        bot is in the same vc as the user, and will
        act accordingly.
        """
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
            if 'open.spotify.com' in query:
                try:
                    author= self.spotify.track(query)
                    artists =author['artists']
                    test = artists[0]
                    name = test['name']
                    query = name + author['name']
                    try: #Tries to see if a music queue already exists in this server
                        guildqueue = self.music_queue[guild]
                    except KeyError: #Makes queue if none exists
                        self.music_queue.update({guild:[]})
                    self.music_queue.update({guild :guildqueue.append(query)})
                    print("here ----------------------")
                    print(guildqueue)
                except SpotifyException:
                    if 'open.spotify.com' in query:
                        author= self.spotify.playlist(query)
                        tracks = author['tracks']
                        items = tracks['items']
                        for i in range(len(items)):#For each item in playlist adds to queue
                            artists = items[i]
                            track = artists['track']
                            artist = track['artists']
                            whichone = artist[0] #gets the 1st artist from the lists of artists
                            author = whichone['name']
                            name = track['name']
                            query = name + ' '+  author #adds auth name to queue to look up
                            try: #Tries to see if a music queue already exists in this server
                                guildqueue = self.music_queue[guild]
                                if isinstance(guildqueue, list):
                                    guildqueue = []
                            except KeyError: #Makes queue if none exists
                                self.music_queue.update({guild:[]})
                            guildqueue = self.music_queue[guild]
                            guildqueue.append(query)
                        self.music_queue.update({guild:guildqueue})
                        await self.join(ctx) # Makes the bot join the discord channel
                        await self.play_music(ctx) #Makes the bot play the items in queue
                        embed=discord.Embed(
                                            title= "Spotify",
                                            color=0xFF5733,
                                            type = 'rich',
                                            description = "Added all items to the queue"
                                        )
                        await ctx.send(embed = embed)
                        return ctx
            song =  self.search_yt(query)
            if isinstance(song,bool): #Checks if search query works
                embed=discord.Embed(
                                        title= "Error",
                                        color=0xFF5733,
                                        type = 'rich',
                                        description = "Could not download song"
                                    )
                await ctx.send(embed = embed)
                return
            else:
                #adds inputed song to the bot
                try:
                    guildqueue = self.music_queue[guild] #Checks if queue exists
                except KeyError:
                    guildqueue = []
                if not isinstance(guildqueue,list):
                    guildqueue = []
                guildqueue.append(song['title'])
                self.music_queue.update({guild:guildqueue})
                self.queued_title =  song['title']
                image = song['image']
                if self.is_playing is True:
                    message =  self.queued_title + " is added to the queue"
                    embed=discord.Embed(
                                    title= "Queue",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = message
                                    )
                    embed.set_thumbnail(url = image)
                    await ctx.send(embed = embed)
                embed=discord.Embed(
                                    title = "Queue",
                                    description = self.queued_title +" has been added to queue",
                                    color=0xFF5733,
                                    type = 'rich'
                                    )
                embed.set_thumbnail(url = image)
                if  self.is_playing is False:
                    try:
                        await self.join(ctx)
                        await self.play_music(ctx)
                        await ctx.send(embed = embed)
                    except ClientException:
                        await self.play_music(ctx)
                        await ctx.send(embed = embed)
            try:
                if  self.players[guild] == self.voice_channel:
                    print("in same vc")
            except KeyError:
                await self.join(ctx)
                await self.play_music(ctx)
            if  self.players[guild] == self.voice_channel:
                print("in same vc")
            else:
                await self.players[guild].move_to(self.voice_channel)

    @commands.command(aliases = ['q', "Q", "QUEUE", "Queue"],
    help="Displays the current songs in queue; another name is queue")
    async def queue(self, ctx):
        """
        This function gets the queue of items
        and then sends an embeded message with
        all items in the queue.

        It will 1st send an embeded message
        of whatever item is currently playing in
        the queue, the lenght of the queue,
        whatever user asked for the song,
        and how long the song is.

        Then it will send a message with
        all items in the queue labeled with
        their position.
        """
        guild = ctx.guild
        print("here")
        print(self.music_queue[guild])
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
            if self.is_playing is True:
                nextsong = self.playing[guild]
                embed = discord.Embed(
                                    title = "Now VOICE_CLIENTS",
                                    description = nextsong['title']
                                    )
                seconds = nextsong['duration']
                hours, seconds = divmod(seconds, 60 ** 2)
                minutes, seconds = divmod(seconds, 60)
                time = '{:02}:{:02}:{:02}'.format(hours, minutes, seconds)
                embed.add_field(name="Duration",
                                value=time,
                                inline=True)
                embed.add_field(name="Queue Length",
                                value=len(self.music_queue[guild])+1,
                                inline=True)
                embed.add_field(name = "URL",
                                value='[Click For Link](' +nextsong['url']+' )')
                embed.add_field(name="Requested by",
                                value="<@" + str(ctx.author.id)+">",
                                inline=True)
                embed.set_image(url = nextsong['image'])
                nextsong = nextsong['source']
                await ctx.send(embed = embed)
            if len( self.music_queue)>0:
                for i in range(len(self.music_queue[guild])):
                    retval = retval + (str(i+1) + ': ' + guildqueue[i] + "\n")
                embed=discord.Embed(
                                    title="Queue",
                                    description=retval,
                                    color=0xFF5733)
                await ctx.send(embed=embed)
        else:
            if self.players[guild].is_playing():
                nextsong = self.playing[guild]
                embed = discord.Embed(
                                    title = "Now VOICE_CLIENTS",
                                    description = nextsong['title']
                                    )
                seconds = nextsong['duration']
                hours, seconds = divmod(seconds, 60 ** 2)
                minutes, seconds = divmod(seconds, 60)
                time = '{:02}:{:02}:{:02}'.format(hours, minutes, seconds)
                embed.add_field(name="Duration",
                                value=time,
                                inline=True)
                embed.add_field(name="Queue Length",
                value=len(self.music_queue[guild])+1,
                        inline=True)
                embed.add_field(name = "URL",
                                value='[Click For Link](' +nextsong['url']+' )')
                embed.add_field(name="Requested by",
                                value="<@" + str(ctx.author.id)+">",
                                inline=True)
                embed.set_image(url = nextsong['image'])
                nextsong = nextsong['source']
                await ctx.send(embed = embed)
            embed=discord.Embed(
                                    title="Queue",
                                    description="There are no items currently in the queue",
                                    color=0xFF5733
                                    )
            await ctx.send(embed=embed)
    #Skip command
    @commands.command(aliases = ['s', '-skip','next','n'],
                help="Skips the current song being played; other names are next, n, or s")
    async def skip(self, ctx):
        """
        Skips the item that is currently
        plaing in queue, and plays the next
        item in queue.
        """
        guild = ctx.guild
        if  self.players[guild] != "" and  self.players[guild]:
            self.players[guild].stop()
            #try to play next in the queue if it exists
            await self.play_music(ctx)
            self.times_skipped = self.times_skipped+1
            print(self.times_skipped)
    #Move command
    @commands.command(aliases = ['m', "M", "MOVE"],
                    help = "Changes the queue placement; another name is move")
    async def move(self, ctx, end, start):
        """
        This function is used to move an item in the queue.
        The user can only use the position of the items to move them.
        """
        to_loc = int(start)
        fromvar = int(end)
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
        if to_loc > fromvar:
            big = to_loc
            small = fromvar
        if to_loc< fromvar:
            big = fromvar
            small = to_loc
        if to_loc == fromvar:
            pass
        else:
            if big < len(guildqueue)+1:
                tempvarbig = (guildqueue[big-1])
                tempvarfrom = (guildqueue[small-1])
                guildqueue.insert(small,tempvarbig)
                guildqueue.insert(big, tempvarfrom)
                guildqueue.pop(big+1)
                guildqueue.pop(small-1)
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

    @commands.command(aliases = ['c', 'r', 'remove', "R", "REMOVE", "C", "CLEAR"],
    help = "Removes all songs the the current queue; other names are clear, r, or remove")
    async def clear(self, ctx, *args):
        """
        This function tkaes in 1 paramater.
        The paramater is used search for the desired
        items to delete.
        If user inputs nothing then it deletes all
        items witin the queue.
        The user may also choose to enter a number in order to
        delete the queued item with said number.
        """
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
        else: #Checks to see if the query is filled out
            if query == "":
                for i in range(len(guildqueue)-1, -1 ,-1):
                    guildqueue.pop(i) # If so then it will remove all items in the queue
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
            else: #if query is str then looks for a match in queue, and removes all items
                try: #tries to see if the user inputed a number
                    query = int(query)
                    if query < len(self.music_queue[guild])+1:
                        guildqueue = self.music_queue[guild]
                        msg = "You removed " +  guildqueue[query-1] + " from the queue"
                        guildqueue.pop(query-1)
                        embed=discord.Embed(
                                    title= "Queue",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = msg
                                    )
                        await ctx.send(embed = embed)
                        self.music_queue.update({guild:guildqueue})
                    else:
                        msg = "Please enter a number smaller than the lenght of the queue"
                        embed=discord.Embed(
                                    title= "Queue",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = msg
                                    )
                        await ctx.send(embed = embed)
                    return query
                except ValueError:
                    times = 0
                    for song in range(len(self.music_queue)+1):
                        if query in  self.music_queue[guild]:
                            times = times +1
                            message = "You removed " +  guildqueue[song] + " from the queue"
                            embed=discord.Embed(
                                    title= "Queue",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = message
                                    )
                            await ctx.send(embed = embed)
                            guildqueue.pop(song)
                        if query not in self.music_queue[song] and times == 0:
                            embed=discord.Embed(
                                    title= "Error",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Enter a value within the queue"
                                    )
                            await ctx.send(embed =embed)
                    self.music_queue.update({guild:guildqueue})
    @commands.command(aliases = ['l', "L", "LEAVE"],
    help = "Makes the bot leave the vc; another name is l")
    async def leave(self, ctx):
        """
        This function is designed to
        make the bot leave the voice channel
        """
        guild =ctx.guild
        if self.players[guild].is_connected():
            try:
                if self.music_queue[guild] != {}:
                    await self.clear(ctx)
            except KeyError:
                self.is_playing = False
            embed=discord.Embed(
                                    title= "Bot",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "Bot left " + str(self.players[guild].channel)
                                    )
            await ctx.send(embed = embed)
            await self.players[guild].disconnect() # Leave the channel
            self.players.pop(guild)
        else:#But if it isn't
            embed=discord.Embed(
                                    title= "Error",
                                    color=0xFF5733,
                                    type = 'rich',
        description = "I'm not currently in a voice channel use the join command to make me join"
                                    )
            await ctx.send(embed =embed)
    #Join command
    @commands.command(aliases = ['j', "J","JOIN", "Join"],
    help = "Makes the bot join; another name is join")
    async def join(self, ctx):
        """
        This function is designed to
        make the bot join whatever
        voice channel the bot is in
        """
        guild = ctx.guild
        if ctx.author.voice: # If the person is in a channel
            channel = ctx.author.voice.channel
            try: # Checks to see if there is a player within that guild
                self.players[guild]
            except KeyError: #If not it will make the bot
                v_c = await channel.connect()
                self.players.update({guild:v_c})
            if self.players == {}: #If there are no PLAYERS currently
                v_c = await channel.connect()
                self.players.update({guild:v_c})
            if ctx.author.voice.channel != self.players[guild]:
                await self.players[guild].move_to(channel)
            else:#runs if not in channel
                v_c=await channel.connect()
                self.players.update({guild: v_c})
        else:
            embed=discord.Embed(
                                    title= "Error",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "You must be in a voice channel for me to join it"
                                    )
            await ctx.send(embed = embed)
    #pause command
    @commands.command(aliases = ['stop', "S", "STOP", "Stop"],
    help = "Makes the bot pause; another name is stop")
    async def pause(self, ctx):
        """
        If the bot is currently
        playing a track
        it will pause the bot.
        """
        guild = ctx.guild
        if  self.music_queue == "":
            embed=discord.Embed(
                                    title= "Error",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is nothing that is currently playing"
                                    )
            await ctx.send(embed = embed)
        else:
            self.players[guild].pause()
    #resume command
    @commands.command(name = 'resume',
    help = "Makes the bot resume VOICE_CLIENTS; can only be acessed with resume")
    async def resume(self, ctx):
        """
        If the bot is paused it will
        resume the bot.
        """
        guild = ctx.guild
        if  self.music_queue == "":
            embed=discord.Embed(
                                    title= "Error",
                                    color=0xFF5733,
                                    type = 'rich',
                                    description = "There is nothing VOICE_CLIENTS now"
                                    )
            await ctx.send(embed = embed)
        else:
            self.players[guild].resume()
    @commands.command(name= 'shuffle',
            help = "Make the queue random; can only be acessed with shuffle")
    async def shuffle(self,ctx):
        """
        Will get a 2 random numbers
        within the size of the queue
        and then moves them.

        It will repeat this as many
        times as how long the queue is.
        """
        guild = ctx.guild
        guildqueue = self.music_queue[guild]
        for i in range(0,len(guildqueue)):
            to_loc = random.randint(1, len(guildqueue))
            fromvar = random.randint(1, len(guildqueue))
            if to_loc > fromvar:
                big = to_loc
                small = fromvar
            if to_loc< fromvar:
                big = fromvar
                small = to_loc
            if to_loc == fromvar:
                pass
            else:
                if big < len(guildqueue)+1:
                    tempvarbig = (guildqueue[big-1])
                    tempvarfrom = (guildqueue[small-1])
                    guildqueue.insert(small,tempvarbig)
                    guildqueue.insert(big, tempvarfrom)
                    guildqueue.pop(big+1)
                    guildqueue.pop(small-1)
        self.music_queue.update({guild:guildqueue})
        guildqueue = []
    @commands.command(aliases = ['PLAY_FILE','pf','PF'],
    help = "plays a file")
    async def play_file(self,ctx,*file):
        """
        Given an input of a discord media
        link it will add the link to the queue
        and try to play it.
        """
        guild = ctx.guild
        try:
            guildqueue = self.music_queue[guild]
        except KeyError:
            guildqueue = []
        guildqueue.append(file)
        self.music_queue.update({guild:guildqueue})
        await self.join(ctx)
        await self.play_music(ctx)
    @commands.command(name = "search",
    help = "looks up the query on yt and shows the 1st 5 options")
    async def search(self,ctx,*args):
        """
        This function takes a user input,
        and then searches it on yt.

        Once it gets 10 items it will
        then ask the user which one out of
        the 10 that they would like to
        add to the music queue.
        """
        query = "".join(args)
        items =pytube.Search(query=query).results
        results = []
        for i in range(len(items)):
            if i < 10:
                results.append(items[i].vid_info["videoDetails"])
        titles = []
        for item in results:
            titles.append(item['title'])
        links = []
        for video in results:
            links.append("https://www.youtube.com/watch?v="+video['videoId'])
        retval = ""
        for int_ in range(len(titles)):
            retval = retval + (str(i+1) + ': '+ '[' + titles[int_]+']'+'('+ links[int_] +')' + "\n")
        embed=discord.Embed(
                                    title="Queue",
                                    description=retval,
                                    color=0xFF5733)
        await ctx.send(embed=embed)
        choice = 0
        msg = await self.bot.wait_for("message",
                        timeout = 60,
                        check = lambda message: message.author ==  ctx.author)
        while True:
            try:
                choice= int(msg.content)
                break
            except ValueError:
                await ctx.send("Please enter a valid number")
                msg = await self.bot.wait_for("message",
                                        timeout = 60,
                        check = lambda message: message.author ==  ctx.author)
        if choice > 10:
            embed=discord.Embed(
                                    title="Error",
                        description="Please enter a number lower than lenght of the search list",
                                    color=0xFF5733)
            await ctx.send(embed=embed)
        print(links)
        await self.play(ctx, links[choice-1])
