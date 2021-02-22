from discord.ext.commands import Bot

from discord_handler.base.cog_owner import BaseOwner


class Owner(BaseOwner):
    """
    Commands available for admins of discord servers.
    """

    def __init__(self, bot: Bot):
        super().__init__(bot)

def setup(bot):
    bot.add_cog(Owner(bot))
