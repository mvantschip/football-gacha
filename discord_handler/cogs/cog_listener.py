import asyncio
import os
import traceback
from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.abc import Request
from discord import RawReactionActionEvent, Guild, Member, TextChannel, Message, Forbidden, NotFound, Reaction, \
    VoiceState, VoiceChannel, HTTPException
from discord.ext.commands import Bot, Cog, Context

from discord_handler.cogs.cog_crawler import Crawler
from db import models
from discord_handler.base.cog_interface import ICog, AuthorState
from discord_handler.helper import get_user, get_guild, get_channel, yes_no, CustCtx

if TYPE_CHECKING:
    from discord_handler.cogs.cog_bot_owner import DBotOwner
    from discord_handler.cogs.cog_all import All

path = os.path.dirname(os.path.realpath(__file__)) + "/../../"


class Listener(ICog):
    """
    Listener commands. Probably only used internally
    """

    def __init__(self, bot: Bot):
        super().__init__(bot, AuthorState.BotOwner)
        self.role_lock = asyncio.Lock()
        self.time = None

    @Cog.listener()
    async def on_command(self, ctx: Context):
        if ctx.author.id == self.bot.user.id:
            return

        text = f"**:hammer_pick:  User {ctx.author.name} ({ctx.author.id}) performed a " \
               f"command on {ctx.author.guild.name}:hammer_pick: :\n\n **"
        text += f"Time: {ctx.message.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Command: **{ctx.message.content}**"

        bot_owner: 'DBotOwner' = self.bot.get_cog('DBotOwner')
        await bot_owner.send_update(text, bot_owner.bot_owner_dm_channel, ctx.guild)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload is None:
            return

        d_g: Guild = self.bot.get_guild(payload.guild_id)
        if d_g is None:
            return
        try:

            user: Member = await d_g.fetch_member(payload.user_id)
            channel: TextChannel = d_g.get_channel(payload.channel_id)

            try:
                message: Message = await channel.fetch_message(payload.message_id)
            except (Forbidden, NotFound):
                return

            emoji = payload.emoji
            try:
                reaction: Reaction = [i for i in message.reactions if i.emoji.id == emoji.id][0]
            except IndexError:
                return
            except AttributeError:
                try:
                    reaction: Reaction = [i for i in message.reactions if i.emoji == emoji.name][0]
                except IndexError:
                    return

            #now everything is prepared

        except Exception as e:
            f = models.Error(g=models.DBGuild.objects.get(g_id=d_g.id)
                             , cmd_string="on raw reaction error", error_type=f'{type(e)}', error=f'{e}',
                             traceback=traceback.format_exc())
            f.save()
            await self.notify_error_bot_owner(f, d_g)

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        try:
            pass
        except Exception as e:
            f = models.Error(g=models.DBGuild.objects.get(g_id=after.guild.id)
                             , cmd_string="on member update", error_type=f'{type(e)}', error=f'{e}',
                             traceback=traceback.format_exc())
            f.save()
            await self.notify_error_bot_owner(f, after.guild)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        try:
            pass
        except Exception as e:
            f = models.Error(g=models.DBGuild.objects.get(g_id=member.guild.id)
                             , cmd_string="on member join", error_type=f'{type(e)}', error=f'{e}',
                             traceback=traceback.format_exc())
            f.save()
            await self.notify_error_bot_owner(f, member.guild)

    @Cog.listener()
    async def on_member_remove(self, member: Member):
        try:
            pass
        except Exception as e:
            f = models.Error(g=models.DBGuild.objects.get(g_id=member.guild.id)
                             , cmd_string="on member.leave", error_type=f'{type(e)}', error=f'{e}',
                             traceback=traceback.format_exc())
            f.save()
            await self.notify_error_bot_owner(f, member.guild)

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        pass

    @Cog.listener()
    async def on_member_ban(self, d_g: Guild, member: Member):
        try:
            pass
        except Exception as e:
            f = models.Error(g=get_guild(d_g)
                             , cmd_string="on member ban error", error_type=f'{type(e)}', error=f'{e}',
                             traceback=traceback.format_exc())
            f.save()
            await self.notify_error_bot_owner(f, d_g)

def setup(bot):
    bot.add_cog(Listener(bot))
