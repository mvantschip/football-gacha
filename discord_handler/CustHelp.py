import asyncio

from discord import Embed, Message, Reaction, Member, NotFound
from discord.ext.commands import HelpCommand, Command, Cog, Bot
from typing import Union, List

from discord_handler.helper import emojiList


class HelpObj():
    def __init__(self, name: str, brief: str, emoji: str = None, help: str = None, obj=None):
        self._name = name
        self._brief = brief
        self._emoji = emoji
        self._help = help
        self._signature = None
        self._obj = obj
        pass

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return f"`{self._name}`"

    @property
    def brief(self):
        return self._brief

    @property
    def emoji(self):
        return self._emoji

    @property
    def help(self):
        return self._help

    @property
    def signature(self):
        return self._signature

    @signature.setter
    def signature(self, value):
        self._signature = value


class EmbedPaginator():
    def __init__(self, help_obj: HelpCommand):
        self._entries = []
        self._help_obj = help_obj
        pass

    def add_command(self, command: Union[Command, Cog], emoji=None):
        if isinstance(command, Cog):
            self._entries.append(HelpObj(command.qualified_name, command.description, emoji, obj=command))
        elif isinstance(command, Command):
            help = "No help available" if not command.help else command.help
            h_obj = HelpObj(command.qualified_name, command.short_doc, emoji, help=help, obj=command)
            h_obj.signature = self._help_obj.get_command_signature(command)
            self._entries.append(h_obj)
        elif isinstance(command, Command) and not command.description:
            self._entries.append(HelpObj(command.qualified_name, command.short_doc, emoji, obj=command))
        elif isinstance(command, Command):
            self._entries.append(
                HelpObj(command.qualified_name, command.short_doc, emoji, help=command.description, obj=command))

    @property
    def entries(self) -> List[HelpObj]:
        return self._entries

    def clear(self):
        self._entries = []

    @property
    def help_description(self):
        return self._help_description

    @help_description.setter
    def help_description(self, value):
        self._help_description = value


class CustHelp(HelpCommand):
    def __init__(self, **options):
        self.width = options.pop('width', 130)
        self.indent = options.pop('indent', 2)
        self.show = options.pop('show', True)
        self.sort_commands = options.pop('sort_commands', True)
        self.dm_help = options.pop('dm_help', False)
        self.dm_help_threshold = options.pop('dm_help_threshold', 1000)
        self.commands_heading = options.pop('commands_heading', "Commands:")
        self.no_category = options.pop('no_category', 'No Category')
        self.paginator = options.pop('paginator', None)

        if self.paginator is None:
            self.paginator = EmbedPaginator(self)

        super().__init__(**options)

    def shorten_text(self, text):
        """Shortens text to fit into the :attr:`width`."""
        if len(text) > self.width:
            return text[:self.width - 3] + '...'
        return text

    def get_ending_cat(self):
        """Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Type {0}{1} category for more info on a category.\n".format(self.clean_prefix, command_name)

    def get_ending_note(self):
        """Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Type {0}{1} command for more info on a command.\n" \
               "You can also type {0}{1} category for more info on a category.".format(self.clean_prefix, command_name)

    def add_indented_commands(self, commands: Union[List[Command], Cog]):
        """Indents a list of commands after the specified heading.

        The formatting is added to the :attr:`paginator`.

        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.

        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        """

        if not commands:
            return

        if isinstance(commands, list):
            for i, emoji in zip(commands, emojiList[:len(commands)]):
                self.paginator.add_command(i, emoji)
        else:
            self.paginator.add_command(commands)

    async def send_pages(self, bot: Union[None, Bot], command_only=False):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""
        if not self.show:
            return

        destination = self.get_destination()
        e = Embed(title="`Bot Help`", description=self.paginator.help_description)
        options = None
        if command_only:
            page = self.paginator.entries[0]
            if page.help and page.help != "No help available":
                e.add_field(name="Description", value=f"`{page.help}`", inline=False)
            elif page.brief:
                e.add_field(name="Description", value=f"`{page.brief}`", inline=False)
            else:
                e.add_field(name="Description", value=f"`No help available`", inline=False)

            if page.signature is not None:
                e.add_field(name="Signature", value=f"`{page.signature}`", inline=False)
        else:
            options = {}
            for page in self.paginator.entries:
                help_text = page.brief
                if not help_text:
                    help_text = "**No help available**"
                e.add_field(name=f"{page.emoji}" + page.name, value=help_text, inline=False)
                options[page.emoji] = page

            e.set_footer(text=f"Type {self.clean_prefix}help on any element or click the associated emoji for "
                              f"detailed help.")

        if bot is None or command_only or options is None:
            await destination.send(embed=e)
        else:
            msg: Message = await destination.send(embed=e)
            for i in options.keys():
                await msg.add_reaction(i)

            def check(reaction: Reaction, user: Member):
                if user.bot:
                    return False
                return reaction.emoji in list(options.keys()) and reaction.message.id == msg.id

            try:
                reaction, _ = await bot.wait_for('reaction_add', check=check,
                                                 timeout=120)
                option = options[reaction.emoji]
                self.paginator.clear()
                await msg.delete()
                if isinstance(option.obj, Cog):
                    await self.send_cog_help(option.obj)
                elif isinstance(option.obj, Command):

                    await self.send_command_help(option.obj)
            except asyncio.TimeoutError as e:
                pass
            finally:
                try:
                    await msg.delete()
                except NotFound:
                    pass

    def get_destination(self):
        ctx = self.context
        return ctx.channel

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        no_category = '\u200b{0.no_category}:'.format(self)

        def get_category(command: Command, *, no_category=no_category):
            cog = command.cog
            return cog
            # return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True)

        # Now we can add the commands to the page.
        cogs = []
        for i in bot.commands:
            cog = get_category(i)
            if cog is None:
                continue
            if await cog.cog_check(ctx):
                cogs.append(cog)
        cogs = list(set(cogs))
        self.add_indented_commands(cogs)

        self.paginator.help_description = "Below you can see all available categories you have access to."

        await self.send_pages(bot)

    async def send_command_help(self, command):
        help_description = f"`{self.clean_prefix}{command.qualified_name}`"
        self.paginator.help_description = help_description
        self.paginator.add_command(command)
        await self.send_pages(None, True)

    async def send_cog_help(self, cog):
        if cog.description:
            help_description = f"Available commands:"
            self.paginator.help_description = help_description
        else:
            self.paginator.help_description = f"Available commands:"

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered)

        await self.send_pages(cog.bot)
