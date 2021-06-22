print("Starting...")

import discord
import sys
from bot import Bot
from commands import Commands



def main(*args):
    client = Bot(
        command_prefix=Bot.get_prefix, 
        help_command=None, 
        intents=discord.Intents().all()
    )
    client.load_commands(Commands)    

    client.run()



if __name__ == '__main__':
    main(*sys.argv[1:])