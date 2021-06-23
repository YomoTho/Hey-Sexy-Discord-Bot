print("Starting...")

import discord
import sys
from bot import Bot
from commands import Owner_Commands, Nc_Commands, Nsfw_Commands, Reddit_Commands, Admin_Commands



def main(*args):
    client = Bot(
        command_prefix=Bot.get_prefix, 
        args=args,
        help_command=None, 
        intents=discord.Intents().all()
    )
    client.load_commands(Owner_Commands, Nc_Commands, Nsfw_Commands, Reddit_Commands, Admin_Commands)    
    
    #client.loop.create_task(client.stats())

    client.run()
        



if __name__ == '__main__':
    main(*sys.argv[1:])