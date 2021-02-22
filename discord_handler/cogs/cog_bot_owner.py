import os

from discord.ext.commands import Bot, command, Context, ExtensionNotLoaded, Cog

from discord_handler.base.cogs_bot_owner import BotOwner

path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'plots')


class DBotOwner(BotOwner):
    """
    Bot owner commands. Debugging functions.
    """

    def __init__(self, bot: Bot, d: dict, extension_list=[]):
        super().__init__(bot, d)
        for i in extension_list:
            bot.load_extension(i)
        self.extension_list = extension_list

    @command(
        name='reload',
        help='Reloads an extension by name'
    )
    async def reload_extension(self, ctx: Context, *, name: str):
        try:
            self.bot.reload_extension(name)
            await ctx.send(f"Reloaded {name}")
        except ExtensionNotLoaded:
            await ctx.send(f"**Can't load {name}**")

    @command(
        name='reload_all',
        help='Reloads all extensions'
    )
    async def reload_all(self, ctx: Context):
        for i in self.extension_list:
            if i == 'discord_handler.cogs.cog_owner':
                continue
            try:
                self.bot.reload_extension(i)
                await ctx.send(f"Reloading {i}")
            except ExtensionNotLoaded:
                await ctx.send(f"**Can't load {i}**")
        await ctx.send("Done")