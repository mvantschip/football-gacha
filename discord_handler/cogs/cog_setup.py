from discord.ext.commands import Bot, command, Context

from discord_handler.base.cog_interface import ICog, AuthorState


class Setup(ICog):
    """
    Setup commands. Use this first when you add the bot to your server.
    """

    def __init__(self, bot: Bot):
        super().__init__(bot, AuthorState.Owner)

    @command(
        name='setup',
        brief='Starts the setup process for IntroBot',
        help='Starts the setup process. This will guide you through the basic channels and settings.'
    )
    async def setup(self, ctx: Context):
        pass


def setup(bot):
    bot.add_cog(Setup(bot))
