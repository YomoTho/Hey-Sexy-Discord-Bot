print("Starting...")

import sys
from bot import Bot
from commands import commands_classes # `commands_classes` - is a list of classes


def main(*args) -> None:
    client = Bot(
        command_prefix=Bot.get_prefix, 
        args=args,
        help_command=None, 
    )
    client.load_commands(*commands_classes)
    
    client.loop.create_task(client.stats())

    client.run()
        



if __name__ == '__main__':
    main(*sys.argv[1:])