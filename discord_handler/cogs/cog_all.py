import json
import os

import inflect
from discord.ext.commands import Bot

from discord_handler.base.cog_interface import ICog, AuthorState

path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')

with open(os.path.join(path, 'secret.json'), 'r') as f:
    d = json.load(f)

p = inflect.engine()


class IntroEndedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class All(ICog):
    """
    Commands that are available to all users on the server. Output may differ between different user levels.
    """

    def __init__(self, bot: Bot):
        super().__init__(bot, AuthorState.User)
        self.intro_running_list = []

def setup(bot):
    bot.add_cog(All(bot))
