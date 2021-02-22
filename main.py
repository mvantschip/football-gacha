# django initial stuff
import argparse
import os

import discord

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

# Ensure settings are read
application = get_wsgi_application()

from discord_handler.CustHelp import CustHelp
from discord_handler.cogs.cog_bot_owner import DBotOwner
from discord_handler.helper import get_guild, get_pre


# discord.py stuff
from discord.ext.commands import Bot
# library stuff
import json
# local
import os
from db.models import Error
import sys
import traceback

def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--split_logic_bot", help="Flag to split the bot and the logic behind",default=False,type=bool)
    parser.add_argument("--type", help="Which type of bot is run",type=str,
                        choices=['bot','worker'],
                        default='bot')
    return parser

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(args)
    intents = discord.Intents(messages=True, guilds=True)
    """
    #use these if necessary
    intents.reactions = True
    intents.members = True
    intents.bans = True
    intents.members = True
    """
    bot = Bot(command_prefix=get_pre,help_command=CustHelp(show=True),intents=intents)
    path = os.path.dirname(os.path.realpath(__file__)) + "/"

    @bot.event
    async def on_error(event, *args, **kwargs):
        try:
            g_obj = args[0].guild
        except AttributeError:
            g_obj = bot.get_guild(args[0].guild_id)
        try:
            g = get_guild(g_obj)
        except AttributeError:
            g = None
        sys_info = sys.exc_info()
        e = Error(g=g, cmd_string=event
                  , error_type=f'{sys_info[0]}', error=f'{sys_info[1]}', traceback=traceback.format_exc())
        e.save()
        bot_owner : 'DBotOwner' = bot.get_cog('DBotOwner')

        await bot_owner.send_error_notification(e, g_obj)


    if sys.platform == "darwin":
        with open(os.path.join(path,'secret_dev.json'),'r') as f:
            d = json.load(f)
    else:
        with open(os.path.join(path,'secret.json'),'r') as f:
            d = json.load(f)

    bot.add_cog(DBotOwner(bot,d,[
        'discord_handler.cogs.cog_all',
        'discord_handler.cogs.cog_crawler',
        'discord_handler.cogs.cog_listener',
        'discord_handler.cogs.cog_mod',
        'discord_handler.cogs.cog_owner',
        'discord_handler.cogs.cog_setup',
    ]))
    bot.run(d['discord_secret'])

if __name__ == "__main__":
    main()