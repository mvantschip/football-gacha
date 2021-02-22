import json

from discord.ext.commands import Bot, command, Context, Cog
from discord import DMChannel, Member, File, Guild, TextChannel, Message, Attachment, Embed
from discord.errors import Forbidden
from typing import Union
from django.utils import timezone
import os
import datetime
from texttable import Texttable
from aiohttp.web import Request
import logging

from db.models import Error, GuildStats
from discord_handler.base.cog_interface import AuthorState, ICog
from discord_handler.helper import send_table, get_guild, get_user, send_pm

logger = logging.getLogger(__name__)
path = os.path.dirname(os.path.realpath(__file__)) + "/../../"


class BotOwner(ICog):
    def __init__(self, bot: Bot, d: dict):
        super().__init__(bot, AuthorState.BotOwner)
        if 'bot_owner_id' in d.keys():
            self.bot_owner_id = d['bot_owner_id']
        else:
            self.bot_owner_id = None

        if 'bot_owner_server' in d.keys():
            self.bot_owner_server = d['bot_owner_server']
        else:
            self.bot_owner_server = None

        if 'bot_owner_info_channel' in d.keys():
            self.bot_owner_info_channel = d['bot_owner_info_channel']
        else:
            self.bot_owner_info_channel = None

        if 'bot_owner_images_channel' in d.keys():
            self.bot_owner_image_channel = d['bot_owner_images_channel']
        else:
            self.bot_owner_image_channel = None

        if 'bot_owner_messages_channel' in d.keys():
            self.bot_owner_dm_channel = d['bot_owner_messages_channel']
        else:
            self.bot_owner_dm_channel = None

        if 'dms_id' in d.keys():
            self.dms_id = d['dms_id']
        else:
            self.dms_id = None

        if 'bot-comm-channel' in d.keys():
            self.bot_comm_channel = d['bot-comm-channel']
        else:
            self.bot_comm_channel = None

        if 'bot_owner_bot_join_leave' in d.keys():
            self.bot_join_leave = d['bot_owner_bot_join_leave']
        else:
            self.bot_join_leave = None

    async def get_image_link(self, image_path: str, ctx: Context = None) -> Union[str, None]:
        try:
            if self.bot_owner_server is None:
                raise KeyError()

            owner_guild: Guild = [i for i in self.bot.guilds if i.id == self.bot_owner_server][0]
            owner_channel: TextChannel = [i for i in owner_guild.channels if i.id == self.bot_owner_image_channel][0]
            if ctx is not None:
                try:
                    msg = await owner_channel.send(file=File(image_path),
                                                   content=f"Image requested by {ctx.author.display_name}, "
                                                           f"at {ctx.message.created_at},"
                                                           f"using the command {ctx.command} on {ctx.guild.name}.")
                except:
                    msg = await owner_channel.send(file=File(image_path))
            else:
                msg = await owner_channel.send(file=File(image_path))
            att: Attachment = msg.attachments[0]
            return att.url
        except (KeyError, Forbidden) as e:
            return None

    @command(
        name='show_errors',
        help='Shows all errors that occured in a given timeframe'
    )
    async def show_errors(self, ctx: Context, nr_of_days: int):
        table = Texttable()
        tabledata = [["Time", "Guild", "CMD string", "Error Type", "Error"]]
        er = Error.objects.filter(time_stamp__gt=(timezone.now() + datetime.timedelta(-nr_of_days))).order_by(
            'time_stamp')
        for i in er:
            i: Error
            in_guild = None
            for j in ctx.bot.guilds:
                if j.id == i.g.g_id:
                    in_guild = j.name
            tabledata.append(
                [f'{i.time_stamp.strftime("%Y-%m-%d %H:%M")}', in_guild, i.cmd_string, i.error_type, i.error])
        table.set_deco(Texttable.VLINES | Texttable.HEADER | Texttable.BORDER)
        table.add_rows(tabledata, True)
        table.set_cols_width([16, 10, 20, 15, 40])
        txt = "```" + table.draw() + "```"
        await send_table(ctx.send, txt)

    async def send_error_notification(self, e: Error, guild: Guild):
        text = f":exclamation: An error occured on {guild.name} ({guild.id}): @here:exclamation: \n\n" \
               f"_cmd string_: {e.cmd_string}\n" \
               f"_error type_: {e.error_type}\n" \
               f"_error_: {e.error}\n" \
               f"_time stamp_: {e.time_stamp}\n" \
               f"_traceback_: {e.traceback}\n"

        await self.send_update(text, self.bot_owner_info_channel, guild, True)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        text = f"✅{guild.me.mention} was added by `{guild.name}({guild.id})`. Member count: `{guild.member_count}`✅"
        await self.send_update(text, self.bot_join_leave, guild)

        g = get_guild(guild)
        GuildStats(g_joined=g, count=1, total_count=len(self.bot.guilds)).save()

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        text = f"❌{guild.me.mention} was removed from `{guild.name}({guild.id})`. Member count: `{guild.member_count}`❌"
        await self.send_update(text, self.bot_join_leave, guild)
        g = get_guild(guild)

        try:
            related_guild_stat = GuildStats.objects.filter(g_joined=g).order_by('timestamp').last()
        except:
            related_guild_stat = None

        GuildStats(g_left=g, related_object=related_guild_stat, count=-1, total_count=len(self.bot.guilds)).save()

    async def send_update(self, text: str, channel: int, guild: Union[Guild, None], always_send=False,
                          embed: Embed = None):
        try:
            if self.bot_owner_server is None or channel is None:
                raise KeyError()

            if guild is not None and guild.id == self.bot_owner_server and not always_send:
                return

            owner_guild: Guild = [i for i in self.bot.guilds if i.id == self.bot_owner_server][0]
            owner_channel: TextChannel = [i for i in owner_guild.channels if i.id == channel][0]
            await send_table(owner_channel.send, text, False, embed=embed)
        except (KeyError, Forbidden) as e:
            if self.bot_owner_id is not None:
                for bot_owner in self.bot_owner_id:
                    u: Member = self.bot.get_user(bot_owner)
                    if u is not None:
                        dm_channel: DMChannel = await u.create_dm()
                        try:
                            await send_table(dm_channel.send, text, False)
                        except Forbidden:
                            pass

    @Cog.listener()
    async def on_ready(self):
        pass

    async def handle_upvote(self, data):
        pass

    async def handle(self, request: Request):
        pass
