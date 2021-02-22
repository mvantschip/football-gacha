import asyncio
import re
from datetime import timedelta
from typing import Union, List, Tuple, TYPE_CHECKING

import pytz
from discord import Guild, Embed, Member, DMChannel, Message, Reaction, TextChannel, Forbidden, HTTPException, Role, \
    VoiceChannel
from discord.ext.commands import Context, Bot
from django.db import IntegrityError
from django.utils import timezone

from db.models import DBGuild, DBUser, DBChannel, DBRole

if TYPE_CHECKING:
    from discord_handler.cogs.cog_bot_owner import DBotOwner

emojiList = [u"\U0001F1E6",  # a
             u"\U0001F1E7",  # b
             u"\U0001F1E8",  # c
             u"\U0001F1E9",  # d
             u"\U0001F1EA",  # e
             u"\U0001F1EB",  # f
             u"\U0001F1EC",  # g
             u"\U0001F1ED",  # h
             u"\U0001F1EE",  # i
             u"\U0001F1EF",  # j
             u"\U0001F1F0",  # k
             u"\U0001F1F1",  # l
             u"\U0001F1F2",  # m
             u"\U0001F1F3",  # n
             u"\U0001F1F4",  # o
             u"\U0001F1F5",  # p
             u"\U0001F1F6",  # q
             u"\U0001F1F7",  # r
             u"\U0001F1F8",  # s
             u"\U0001F1F9",  # t
             u"\U0001F1FA",  # u
             u"\U0001F1FB",  # v
             u"\U0001F1FC",  # w
             u"\U0001F1FD",  # x
             u"\U0001F1FD",  # y
             u"\U0001F1FF"  # z
             ]


def add_guild(ctx: Union[Context, Guild]):
    """
    Stores a guild into the db
    :param ctx: Context from command or Guild object
    """
    try:
        g_id = ctx.guild.id if isinstance(ctx, Context) else ctx.id
    except:
        return False
    g_name = ctx.guild.name if isinstance(ctx, Context) else ctx.name
    try:
        DBGuild.objects.get(g_id=g_id)
    except DBGuild.DoesNotExist:
        DBGuild(g_id=g_id, name=g_name).save()

    return True


async def send_pm(bot: Bot, u: DBUser, text: str, embed: Embed = None):
    member: Member = bot.get_user(u.u_id)
    if member is not None:
        dm_channel: DMChannel = await member.create_dm()
    else:
        return
    try:
        if embed is None:
            await dm_channel.send(text)
        else:
            await dm_channel.send(text, embed=embed)
    except HTTPException:
        pass
    except Exception as e:
        raise e
    finally:
        bot_owner: 'DBotOwner' = bot.get_cog('DBotOwner')
        await bot_owner.send_update(f'Sent to user {u.u_name}({u.u_id})\n\n;;' + text, bot_owner.dms_id,
                                    None, embed=embed)


def get_guild(guild: Guild) -> DBGuild:
    try:
        g = DBGuild.objects.get(g_id=guild.id)
    except DBGuild.DoesNotExist:
        g = DBGuild(g_id=guild.id, name=guild.name)

    g.name = guild.name
    g.save()
    return g


def get_channel(channel: Union[VoiceChannel, TextChannel]):
    g = get_guild(channel.guild)

    try:
        ch_obj = DBChannel.objects.get(channel_id=channel.id, g=g)
    except DBChannel.DoesNotExist:
        ch_obj = DBChannel(channel_id=channel.id, channel_name=channel.name, g=g)

    ch_obj.channel_name = channel.name
    ch_obj.save()
    return ch_obj


def get_role(role: Role):
    g = DBGuild.objects.get(g_id=role.guild.id)
    try:
        dbrole = DBRole.objects.get(g=g, role_id=role.id)
    except DBRole.DoesNotExist:
        dbrole = DBRole(g=g, role_id=role.id)

    dbrole.role_name = role.name
    dbrole.role_color_r = role.color.r
    dbrole.role_color_g = role.color.g
    dbrole.role_color_b = role.color.b
    dbrole.save()
    return dbrole


def get_user(member: Member, g: DBGuild = None) -> DBUser:
    if g is None:
        g = DBGuild.objects.get(g_id=member.guild.id)

    try:
        u = DBUser.objects.get(u_id=member.id, g=g)
        u.d_name = member.display_name
        u.is_bot = member.bot
        u.avatar_url = member.avatar_url
        u.save()
    except DBUser.DoesNotExist:
        try:
            u = DBUser(u_id=member.id, u_name=member.display_name, g=g,
                       is_bot=member.bot,
                       avatar_url=member.avatar_url)
            u.save()
        except IntegrityError:
            u = DBUser.objects.get(u_id=member.id, g=g)
            u.d_name = member.display_name
            u.is_bot = member.bot
            u.avatar_url = member.avatar_url
            u.save()

    return u


async def send_table(send_fun: callable, txt: str, add_raw=True, embed: Embed = None):
    text = [txt[i:i + 1900] for i in range(0, len(txt), 1900)]
    msg_list: List[Message] = []
    if add_raw:
        for i in range(0, len(text)):
            if i == 0 and not text[i].endswith('```'):
                text[i] += "```"
            elif i == len(text) - 1 and not text[i].startswith('```') and i != 0:
                text[i] = "```" + text[i]
            elif not text[i].startswith('```') and not text[i].endswith('```') and i != 0:
                text[i] = "```" + text[i] + "```"

    for text_part in text[:-1]:
        msg_list.append(await send_fun(text_part))

    if embed is not None:
        msg_list.append(await send_fun(text[-1], embed=embed))
    else:
        msg_list.append(await send_fun(text[-1]))

    return msg_list


def pretty_time(time: int):
    if isinstance(time, int) or isinstance(time, float):
        if time == float("inf"):
            return "inf"
        d_time = timedelta(seconds=time)
    else:
        d_time = time
    days, hours, minutes = d_time.days, d_time.seconds // 3600, (d_time.seconds // 60) % 60
    seconds = int(time - (days * 24 * 3600 + hours * 3600 + minutes * 60))
    text = ""

    for val, txt in [(days, 'day'), (hours, 'hour'), (minutes, 'minute'), (seconds, 'second')]:
        if val != 0:
            text += f"{val} {txt}{'' if val == 1 else 's'} "
    return text.strip()


async def get_pre(_, message: Message):
    if not isinstance(message.author, Member):
        return ";"

    author_g_id = message.author.guild.id
    try:
        g = DBGuild.objects.get(g_id=author_g_id)
    except DBGuild.DoesNotExist:
        g = DBGuild(g_id=author_g_id, name=message.author.guild.name)
        g.save()

    return g.prefix


def convert_str_date(time_string: str):
    time = 0
    if "d" in time_string:
        days = re.findall(r"(\d+)d", time_string)[0]
        time += int(days) * 24 * 3600

    if "h" in time_string:
        hours = re.findall(r"(\d+)h", time_string)[0]
        time += int(hours) * 3600

    if "m" in time_string:
        minutes = re.findall(r"(\d+)m", time_string)[0]
        time += int(minutes) * 60

    if "s" in time_string:
        seconds = re.findall(r"(\d+)s", time_string)[0]
        time += int(seconds)

    return time


async def choose_option(ctx: Context, text: str, options: List[object], check_fun: callable = None,
                        mapping_list: List[object] = None, embed: Embed = None):
    if mapping_list is not None and len(mapping_list) != len(options):
        raise ValueError("Mapping list and options must be of same length")

    option_dict = {}
    mapping_dict = {}
    for i, (option, emoji) in enumerate(zip(options, emojiList[:len(options)])):
        text += f"\n{emoji}: {option}"
        option_dict[emoji] = option
        if mapping_list is not None:
            mapping_dict[emoji] = mapping_list[i]

    if embed is None:
        msg: Message = await ctx.send(text)
    else:
        msg: Message = await ctx.send(text, embed=embed)

    for key in option_dict.keys():
        await msg.add_reaction(key)

    def default_check(reaction: Reaction, user: Member):
        if user.bot:
            return False

        if ctx.author is not None and ctx.channel is not None:
            return reaction.emoji in emojiList and user == ctx.author and reaction.message.id == msg.id
        else:
            return reaction.emoji in emojiList and reaction.message.id == msg.id

    check = default_check if check_fun is None else check_fun

    try:
        reaction, _ = await ctx.bot.wait_for('reaction_add', check=check,
                                             timeout=120)
    except asyncio.TimeoutError as e:
        await ctx.send("Sorry you timed out.")
        raise e
    finally:
        await msg.delete()
    if mapping_list is None:
        return option_dict[reaction.emoji]
    else:
        return mapping_dict[reaction.emoji]


async def get_response(ctx: Context, text: str, check_fun: callable = None, conversion_fun: callable = None,
                       must_contain_file=False, send_obj=None, timeout=120) -> Tuple[str, Message]:
    send_obj = send_obj if send_obj is not None else ctx
    msg: Message = await send_obj.send(text)

    def default_check(message: Message):
        if not must_contain_file:
            return message.author == ctx.author and message.channel == ctx.channel
        else:
            return message.author == ctx.author and message.channel == ctx.channel and len(message.attachments) == 1

    check = default_check if check_fun is None else check_fun
    tries = 0
    while True:
        try:
            message_answer: Message = await ctx.bot.wait_for('message', check=check,
                                                             timeout=timeout)
            if conversion_fun is not None:
                try:
                    answer = conversion_fun(message_answer.content)
                    break
                except:
                    await send_obj.send("Sorry i couldn't understand that. Please try again.")
                    tries += 1
            else:
                answer = message_answer.content
                break

        except asyncio.TimeoutError as e:
            raise e

        if tries >= 5:
            await send_obj.send("Too many tries. Stopping.")
            raise asyncio.TimeoutError()

    return answer, message_answer


async def yes_no(text: str, ctx: Context, skip=False, embed: Embed = None, timeout=200, timeout_message=True,say_cancelled = True):
    if embed is None:
        msg = await ctx.send(text)
    else:
        msg = await ctx.send(text, embed=embed)
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    em_list = ['✅', '❌']
    if skip:
        await msg.add_reaction('⏩')
        em_list.append('⏩')
    await asyncio.sleep(0.5)

    def r_check(reaction: Reaction, user: Member):
        return reaction.message.id == msg.id and user == ctx.author and str(reaction.emoji) in em_list

    try:
        reaction, _ = await ctx.bot.wait_for('reaction_add', check=r_check, timeout=timeout)
    except asyncio.TimeoutError:
        try:
            await msg.clear_reactions()
        except Forbidden:
            pass
        if timeout_message:
            await ctx.send("Sorry, you timed out.")
        if skip:
            return None
        return False

    if reaction.emoji == '⏩':
        return None

    if reaction.emoji == '❌':
        if say_cancelled:
            await ctx.send("Cancelled.")
        return False

    return True


class CustCtx:
    def __init__(self, guild: Guild, send_fun: callable, channel: Union[TextChannel, DMChannel], author: Member,
                 bot: Bot):
        self._guild = guild
        self._send_fun = send_fun
        self._author = author
        self._channel = channel
        self._bot = bot
        self._message = None

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        if self._send_fun is not None:
            return await self._send_fun(content=content, tts=tts, embed=embed, file=file, files=files,
                                        delete_after=delete_after,
                                        nonce=nonce)
        else:
            return None

    @property
    def guild(self):
        return self._guild

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def channel(self):
        return self._channel

    @property
    def bot(self):
        return self._bot

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    @staticmethod
    async def from_member_dm(m: Member, bot: Bot):
        dm = await m.create_dm()
        return CustCtx(m.guild, dm.send, dm, m, bot)

    @staticmethod
    def from_guild(d_g: Guild, channel_id: Union[int, None], bot: Bot, member: Member = None):
        if channel_id is not None:
            channel: Union[TextChannel, None] = d_g.get_channel(channel_id)
            send = channel.send
        else:
            channel = None
            send = None
        return CustCtx(d_g, send, channel, member, bot)

    @staticmethod
    def from_channel(channel: TextChannel, bot: Bot, member: Member = None):
        return CustCtx(channel.guild, channel.send, channel, member, bot)
