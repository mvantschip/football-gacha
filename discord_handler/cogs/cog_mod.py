import os

from discord.ext.commands import Bot
from discord_handler.base.cog_interface import ICog, AuthorState

path = os.path.dirname(os.path.realpath(__file__)) + "/../../"


class Mod(ICog):
    """
    All commands related to moderation of discord servers.
    """

    def __init__(self, bot: Bot):
        super().__init__(bot, AuthorState.Mod)


def setup(bot):
    bot.add_cog(Mod(bot))
