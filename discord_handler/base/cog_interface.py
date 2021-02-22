import asyncio

from discord.ext.commands import Cog, Bot, Context
from discord import Member, Guild
from discord.ext.commands.errors import *
from discord.errors import Forbidden

from discord_handler.helper import add_guild, get_user, send_pm

from db import models
from db.models import DBGuild, DBUser, Error
import traceback
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from discord_handler.cogs.cog_bot_owner import DBotOwner


class AuthorState:
    User = 1
    Mod = 3
    Owner = 4
    BotOwner = 5


class ICog(Cog):
    def __init__(self, bot: Bot, min_perm: int):
        self.bot = bot
        self.min_perm = min_perm

    async def cog_check(self, ctx):
        perm = await self.a_perm(ctx)
        return perm >= self.min_perm

    async def notify_error_bot_owner(self, e: Error, ctx: Union[Context, Guild]):
        bot_owner: 'DBotOwner' = self.bot.get_cog('DBotOwner')
        if isinstance(ctx, Context):
            await bot_owner.send_error_notification(e, ctx.guild)
        elif isinstance(ctx, Guild):
            await bot_owner.send_error_notification(e, ctx)

    async def cog_command_error(self, ctx: Union[Context, Guild], error: CommandError):
        g_id = ctx.guild.id if isinstance(ctx, Context) else ctx.id
        g_name = ctx.guild.name if isinstance(ctx, Context) else ctx.name
        try:
            g = DBGuild.objects.get(g_id=g_id)
            g.name = g_name
        except DBGuild.DoesNotExist:
            g = DBGuild(id=g_id, name=g_name)

        g.save()

        if isinstance(error, CheckFailure):
            if isinstance(error, BotMissingPermissions):
                text = "To use this command, the bot needs the following permissions:\n"
                for i in error.missing_perms:
                    text += f"**- {i}**\n"
                text += "Please make sure that these are available to the bot."
                await ctx.send(text)

                guild = ctx.guild
                me = guild.me if guild is not None else ctx.bot.user
                permissions = ctx.channel.permissions_for(me)

                e = Error(g=g, cmd_string=ctx.message.system_content
                          , error_type=f'{type(error)}', error=f'{error}', traceback=f"Has : "
                                                                                     f"{permissions}\n\nNeeds: "
                                                                                     f"{error.missing_perms}")
                e.save()
                await self.notify_error_bot_owner(e, ctx)
            else:
                await ctx.send('** Error **: You are not allowed to use this command!')
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f"** Error **: Command _**{ctx.command.qualified_name}**_ misses some arguments."
                           f" See the help:")
            await ctx.send_help(ctx.command)

        elif isinstance(error, ConversionError):
            await ctx.send(f'** Error **: Cannot convert arguments for _**{ctx.command.qualified_name}**_. '
                           'Please make sure, you use the correct types. See the help:')
            await ctx.send_help(ctx.command)

        elif isinstance(error, BadArgument):
            await ctx.send(f'** Error **: Bad Argument for _**{ctx.command.qualified_name}**_! Please '
                           f'check help.')
            await ctx.send_help(ctx.command)

        # TODO improve this
        elif isinstance(error.original, Forbidden):
            text = f'** Error **: Permissions missing for the Bot. The bot needs at least\n' \
                   f'__Manage Roles__\n' \
                   f'__Manage Channels__\n' \
                   f'__Send Messages__\n' \
                   f'__Manage Messages__\n' \
                   f'__Read message history__\n' \
                   f'__Add reactions__\n' \
                   f'Total integer value: 268511344\n' \
                   f'Please make sure that these permissions are given to the bot.'
            try:
                await ctx.send(text)
            except Forbidden:
                try:
                    await send_pm(self.bot, get_user(ctx.author), text)
                except Forbidden:
                    pass

                e = Error(g=g, cmd_string=ctx.message.system_content
                          , error_type=f'{type(error.original)}', error=f'{error}', traceback=traceback.format_exc())
                e.save()
                await self.notify_error_bot_owner(e, ctx)
        elif isinstance(error.original, asyncio.TimeoutError):
            await ctx.send("Timeout")
        else:
            e = Error(g=g, cmd_string=ctx.message.system_content
                      , error_type=f'{type(error.original)}', error=f'{error}', traceback=traceback.format_exc())
            e.save()
            await self.notify_error_bot_owner(e, ctx)
            await ctx.send(f'An error has occured. If this persists, please notify the bot owner.')

    async def cog_before_invoke(self, ctx: Context):
        add_guild(ctx)
        self.g = DBGuild.objects.get(g_id=ctx.guild.id)
        self.m: Member = ctx.author
        self.u: DBUser = get_user(ctx.author)
        try:
            self.u_perm_state = await self.a_perm_intern(self.u, self.m)
        except AttributeError:
            self.m = None
            self.u_perm_state = AuthorState.User

        try:
            cog = models.Cog.objects.get(name=ctx.cog.qualified_name)
        except models.Cog.DoesNotExist:
            cog = models.Cog(name=ctx.cog.qualified_name)
            cog.save()

        try:
            command = models.Command.objects.get(cog=cog, name=ctx.command.name)
        except models.Command.DoesNotExist:
            command = models.Command(cog=cog, name=ctx.command.name)
            command.save()

        models.CommandStats(g=self.g, command=command, user=self.u, parameters=" ".join(
            [f"{ctx.command.clean_params[i]}" for i in ctx.command.clean_params.keys()])).save()

    async def a_perm(self, ctx: Context):
        if not add_guild(ctx):
            return False
        g = DBGuild.objects.get(g_id=ctx.guild.id)
        u = get_user(ctx.author, g)
        member = ctx.author
        return await self.a_perm_intern(u, member)

    async def a_perm_intern(self, u: DBUser, member: Member):
        if await self.is_bot_owner(member):
            return AuthorState.BotOwner
        elif await  self.is_admin(member):
            return AuthorState.Owner
        elif await self.is_mod(u, member):
            return AuthorState.Mod
        else:
            return AuthorState.User

    async def is_admin(self, member: Member):
        return member.guild_permissions.administrator or member.guild_permissions.manage_roles

    async def is_bot_owner(self, member: Member):
        if member is None:
            return False
        bot_owner: 'DBotOwner' = self.bot.get_cog('DBotOwner')
        return member.id in bot_owner.bot_owner_id

    async def is_mod(self, u: DBUser, member: Member):
        if u is not None:
            mod_role = u.g.m_role()
            mod_flag = u.g_mod
            if mod_role is not None and member is not None:
                role_ids = [i.id for i in member.roles]
                mod_role = len([i for i in mod_role if i in role_ids]) > 0
            else:
                mod_role = False

            mod = mod_flag or mod_role
        else:
            mod = False

        return mod or member.guild_permissions.ban_members

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        add_guild(guild)
