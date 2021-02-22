import os
import traceback

from discord import Guild
from discord.ext import tasks
from discord.ext.commands import Bot

from discord_handler.base.cog_interface import ICog, AuthorState
from discord_handler.helper import get_guild
from db import models

path = os.path.dirname(os.path.realpath(__file__)) + "/../../"


class Crawler(ICog):
    """
    Crawler commands. This should only be used internally
    """

    def __init__(self, bot: Bot):
        super().__init__(bot, AuthorState.BotOwner)
        self.dummy_task.start()

    @tasks.loop(minutes=30)
    async def dummy_task(self):
        for d_g in self.bot.guilds:
            d_g: Guild
            try:
                pass
                #Some function can be called here for every guild
            except Exception as e:
                d_g = self.bot.guilds[0]
                f = models.Error(g=get_guild(d_g)
                                 , cmd_string=f"Dummy task error {d_g.name}", error_type=f'{type(e)}', error=f'{e}',
                                 traceback=traceback.format_exc())
                f.save()
                await self.notify_error_bot_owner(f, d_g)

    @dummy_task.before_loop
    async def before_dummy_task(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Crawler(bot))
