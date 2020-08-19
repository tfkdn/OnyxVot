import os
import shutil

import discord
import youtube_dl
from discord.ext import commands
from discord.utils import get

from .Song import Song
from .Queue import Queue
from .utils import download_song_ydl, download_song_ydl_no_pp
from .._menus_for_list import menus, QueueListSource


class VoiceCog(commands.Cog, name="voice"):

    def __init__(self, bot):
        self.bot = bot
        self.embed_colour = 1741991
        self.server_queues = {}
        # 15641651954 : Queue(queue: - - - -,
        #                     path: - - - -)

    #
    #
    #
    #
    #
    #
    #
    #
    #
    #

    @commands.command()
    async def join(self, ctx):
        global voice
        v_channel = ctx.author.voice.channel

        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(v_channel)

        else:
            voice = await v_channel.connect()

        await ctx.send(f"Connection Established to {v_channel}")

    #
    #
    #
    #
    #

    @commands.command()
    async def leave(self, ctx):
        v_channel = ctx.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            print(f"Bot disconnected from {v_channel}")
            await ctx.send(f"Connection to {v_channel} terminated")

        else:
            print("Bot was told to leave but wasn't connected")
            await ctx.send(f"No connection present")

    #
    #
    #
    #
    #

    @commands.command()
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            print("Audio paused")
            voice.pause()
            await ctx.send(f"Audio paused...")

        else:
            print("Audio not playing failed pause")
            await ctx.send("Audio not playing failed pause")

    #
    #
    #
    #
    #

    @commands.command()
    async def resume(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            print("Resumed audio...")
            voice.resume()
            await ctx.send(f"Resumed audio...")

        else:
            print("Audio is not paused")
            await ctx.send("Audio is not paused")

    #
    #
    #
    #
    #

    @commands.command()
    async def skip(self, ctx, tracks_to_skip=None):
        """
        Skip the playing track or n number of tracks to skip
        """
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        queue_obj = self.server_queues[ctx.guild.id]

        if tracks_to_skip:
            queue_obj.song_num += int(tracks_to_skip)

        if voice and voice.is_playing():
            voice.stop()
            await ctx.send(f"Track skipped")

        else:
            print("Audio not playing failed skip")
            await ctx.send("Audio not playing failed skip")

    #
    #
    #
    #
    #
    #
    #
    #
    #
    #

    def check_queue(self, guild_id):
        try:

            queue_obj = self.server_queues[guild_id]

            voice.play(discord.FFmpegPCMAudio(queue_obj.get_song_to_play().path),
                       after=lambda e: self.check_queue(guild_id))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.07

        except Exception as e:
            raise commands.BadArgument(f"{e}")

    #
    #
    #
    #
    #

    @commands.command(aliases=["p"])
    async def play(self, ctx, url: str = ""):
        guild_id = ctx.guild.id
        queue_fld_path = os.path.join(os.path.dirname(__file__), "queue", str(guild_id))
        queue_is_dir = os.path.isdir(queue_fld_path)

        global voice
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if not voice:
            v_channel = ctx.author.voice.channel
            voice = await v_channel.connect()

        if voice and voice.is_playing():  # If it's connected and playing

            queue_obj = self.server_queues[guild_id]

            msg = await ctx.send("Attempting to add")

            song_in_queue = [song for num, song in queue_obj.queue.items() if song.link == url]

            if song_in_queue:
                print("adding repeating")
                queue_obj.add_track(song_in_queue[0])

            else:
                print("adding new")
                queue_obj.add_track(Song(link=url, dl_path=queue_fld_path))

            await msg.edit(content=f"Added to queue ✅")

        elif voice and not voice.is_playing() and not voice.is_paused():  # If not connected and not playing

            self.song_num = 1

            msg = await ctx.send("Attempting to play...")

            if queue_is_dir:
                await msg.edit(content=f"Queue init...")
                shutil.rmtree(queue_fld_path)
                os.mkdir(queue_fld_path)
                await msg.edit(content="Downloading song...")


            self.server_queues[guild_id] = Queue(queue_fld_path)
            queue_obj = self.server_queues[guild_id]
            queue_obj.add_track(Song(link=url, dl_path=queue_fld_path))

            await msg.edit(content="Song downloaded...")

            if not voice or not voice.is_connected():
                v_channel = ctx.author.voice.channel
                voice = await v_channel.connect()

            voice.play(discord.FFmpegPCMAudio(queue_obj.get_song_to_play().path),
                       after=lambda e: self.check_queue(guild_id))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.07

            await msg.edit(content="Playing Track ✅")

    #
    #
    #
    #
    #

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        queue_obj = self.server_queues[ctx.guild.id]

        queue_ls = []
        SongLinks = [s.link for k, s in queue_obj.queue.items()]

        for url in SongLinks:
            with youtube_dl.YoutubeDL() as ydl:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get("title", None)

            queue_ls.append(title)

        source = QueueListSource(queue_ls, self.embed_colour, self.loop)

        menu = menus.MenuPages(source, clear_reactions_after=True)
        await menu.start(ctx)

    #
    #
    #
    #
    #

    @commands.command()
    @commands.is_owner()
    async def queue_ls(self, ctx):

        queue_ls = [self.queue[a] for a in range(1, len(self.queue) + 1)]

        await ctx.send(queue_ls)

    #
    #
    #
    #
    #

    @commands.command()
    async def loop(self, ctx):
        queue_obj = self.server_queues[ctx.guild.id]

        if not queue_obj.loop:
            queue_obj.loop = True
            await ctx.send(f"Looping through the queue")

        else:
            queue_obj.loop = False
            await ctx.send(f"No longer looping through the queue")

    #
    #
    #
    #
    #

    @commands.command(aliases=["np"])
    async def now_playing(self, ctx):
        queue_obj = self.server_queues[ctx.guild.id]

        e = discord.Embed(title="Now playing...",
                          colour=self.embed_colour)

        with youtube_dl.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(queue_obj.get_playing().link, download=False)
            title = info_dict.get("title", None)
            thumbnail = info_dict.get("thumbnail", None)
            e.set_image(url=thumbnail)

        e.add_field(name=f"{queue_obj.song_num}. {queue_obj.get_playing().link}",
                    value=f"{title}")

        await ctx.send(embed=e)

    #
    #
    #
    #
    #

    @commands.command(aliases=["prune", "rm_song"])
    async def prune_song(self, ctx, song_num):

        queue_obj = self.server_queues[ctx.guild.id]

        try:
            await ctx.send(embed=discord.Embed(title=f"Removed the song number {song_num} from the queue",
                                               description=queue_obj[int(song_num)].link,
                                               colour=self.embed_colour))

            queue_obj.rm_track(song_num)

        except KeyError:
            await ctx.send(embed=discord.Embed(title="That song is not on the queue",
                                               colour=self.embed_colour))

    #
    #
    #
    #
    #
    #
    #
    #
    #
    #

    async def cog_check(self, ctx):
        voice_c = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_c and ctx.channel.type != "private":
            if ctx.author.voice.channel == voice_c.channel and voice_c:
                return True
            else:
                return False
        else:
            return True


def setup(bot):
    bot.add_cog(VoiceCog(bot))
    print("VoiceCog has been loaded")
