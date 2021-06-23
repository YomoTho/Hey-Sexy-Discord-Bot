import discord
import os
from discord import Color
from discord.ext import commands
try:
    from scripts.data import Data, MyChannel, Reference
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Reference



class Bot_Commands:
    def __init__(self, client) -> None:
        self.client = client
        self.reference = Reference(client)


    def command(self, *args, **kwargs):
        return self.client.command(*args, **kwargs)



class Owner_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)

        
        @self.command(help='Command testing')
        @commands.is_owner()
        async def test(ctx, *args, **kwargs):
            await ctx.send("%s %s" % (args, kwargs))


        @self.command(help='Server add text channel')
        @commands.is_owner()
        async def sat(ctx, channel:discord.TextChannel, cname:str):
            client.server.add_text_channel(channel, cname)
            
            await client.command_success(ctx.message)


        @self.command(help='Enable text channels')
        @commands.is_owner()
        async def enable(ctx, *channels):
            channels = self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).enable())
            else:
                await ctx.send('\n'.join(reply))


        @self.command(help='Disable text channels')
        @commands.is_owner()
        async def disable(ctx, *channels):
            channels = self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).disable())
            else:
                await ctx.send('\n'.join(reply))


        @self.command(help='List disabled channels')
        @commands.is_owner()
        async def listd(ctx):
            reply = []
            with Data.R('config') as config:
                for ch_id in config['disabled_channels']:
                    reply.append(client.get_channel(ch_id).mention)

            return await ctx.send(
                embed=discord.Embed(
                    title='Disabled Text Channels:',
                    description='\n'.join(reply),
                    colour=Color.from_rgb(255, 0, 0)
                )
            )


        @self.command(help='Restart the bot')
        @commands.is_owner()
        async def reboot(ctx, *args):
            arguments = {'update': self.update_bot, 'clear': self.clear_sceen}

            for arg in args:
                try:
                    await arguments[arg](ctx)
                except KeyError as e:
                    raise Exception("Argument %s not found." % e)
            
            await ctx.send("Rebooting...")
            
            with open('reboot_id', 'w') as f:
                f.write(str(ctx.channel.id))

            await client._exit()



    """
    Commands functions:
    """

    # reboot command
    async def update_bot(self, ctx):
        await ctx.send("**Updating...**")
        _code = os.system('echo $(git pull) > update.txt')
        with open('update.txt') as f:
            update_status = f.read()
        
        await ctx.send(embed=discord.Embed(title='Update status:', description='```\n%s```' % update_status).set_footer(text='exit_code: %s' % _code))
        
        with open('update.txt', 'w') as f:
            pass

    
    # reboot command
    async def clear_sceen(self, ctx):
        os.system('clear')
        print(ctx.channel, ctx.author)


    # enable disable commands
    def get_channels_from_tuple(self, *channels):
        _channels = []
        for channel in channels:
            if channel.startswith('<#') and channel.endswith('>'):
                _channels.append(self.client.get_channel(int(channel[2:-1])))
            else:
                raise Exception("%s is not a channel." % channel)
        else:
            return _channels



class Nsfw_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='NSFW', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(help='r/boobs')
        @commands.is_nsfw()
        async def boobs(ctx, limit:int=1):
            await self.client.reddit(ctx, 'boobs', limit)


        @self.command(help='r/ass')
        @commands.is_nsfw()
        async def ass(ctx, limit:int=1):
            await self.client.reddit(ctx, 'ass', limit)



class Reddit_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='REDDIT', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(name='r/', help='Get post from reddit.')
        async def r(ctx, subreddit:str, limit:int=1):
            await self.client.reddit(ctx, subreddit, limit)



class Nc_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)
        
        """
        No category commands:
        """
        @self.command(help="To see this message.")
        async def help(ctx, command:str=None):
            member = ctx.author
            categories = client.categories.copy()

            categories = self.help_category_check(ctx, member, categories)

            embed = discord.Embed(colour=Color.purple())

            if command is None:
                embed.title = 'All categories:'
                embed = self.help_get_categories(embed, categories)
                embed.set_footer(text='%shelp <category_name>' % client.prefix)
            elif command.lower() == 'all':
                embed.title = "All commands:"
                embed = self.help_get_all_commands(embed, categories)
                embed.set_footer(text='%shelp <command_name>' % client.prefix)
            else:
                if command.upper() in categories:
                    embed = self.help_get_all_commands(embed, {command.upper(): categories[command.upper()]})
                else:
                    found = False
                    for category_name, commands in categories.items():
                        if command in commands:
                            found = True
                            embed.add_field(
                                name=category_name,
                                value='```%s%s %s```%s' % (
                                    await client.get_prefix(ctx.message), 
                                    command, 
                                    commands[command]['args'],
                                    commands[command]['help']
                                ), 
                                inline=False
                            )
                            break
                    else:
                        if not found:
                            return await ctx.message.reply(
                                embed=discord.Embed(
                                    description="""Command "**%s**" not found.""" % command
                                ).set_footer(
                                    text='%shelp <command_name>' % client.prefix
                                )
                            )


            await ctx.send(embed=embed)


        @self.command(help="My latency")
        async def ping(ctx):
            return await ctx.message.reply(
                embed=discord.Embed(
                    description="**%i**ms" % round(client.latency * 1000),
                    colour=Color.blue()
                )
            )


    """
    Commands functions:
    """

    # help command
    def help_category_check(self, ctx, member:discord.Member, categories:dict) -> dict:
        """
        from help command:

        Just checks the member's permissions and deletes the categories
        """

        if not member.id == ctx.guild.owner.id:
            del categories['OWNER']
        if not member.guild_permissions.administrator:
            del categories['ADMIN'] 
        if not 'NSFW' in [role.name for role in member.roles if role.name == 'NSFW']:
            del categories['NSFW']

        return categories


    # help command
    def help_get_categories(self, embed:discord.Embed, categories:dict) -> discord.Embed:
        """
        From help command:

        if command is None:
            get_all_category
        """

        for category_name, commands in categories.items():
            embed.add_field(name=category_name, value='`%i commands`' % len(commands), inline=False)

        return embed


    # help command
    def help_get_all_commands(self, embed:discord.Embed, categories:dict) -> discord.Embed:
        """
        From help command:

        if command == 'all':
            help_get_all_commands
        """

        for category_name, commands in categories.items():
            embed.add_field(
                name=category_name,
                value='```{}```'.format(self.list_commands(commands)),
                inline=False
            )
        else:
            return embed


    # help command
    def left_right(self, left_text:str, right_text:str, space:int=10) -> str:
        return "%s%s%s" % (left_text, ' ' * (space - len(left_text)), right_text)

    
    #help command
    def list_commands(self, commands) -> str:
        return '\n'.join([self.left_right(str(cmd), commands[cmd]['help']) for cmd in commands])









