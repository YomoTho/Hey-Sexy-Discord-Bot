import discord
from discord import Color
from discord.ext import commands
try:
    from scripts.data import Data, MyChannel, Server, Reference
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Server, Reference



class Commands:
    def __init__(self, client) -> None:
        self.client = client
        command = client.command
        reference = Reference(client)

        
        """
        No category commands:
        """
        @command(help="To see this message.")
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


        @command()
        async def ping(ctx):
            return await ctx.message.reply(
                embed=discord.Embed(
                    description="**%i**ms" % round(client.latency * 1000),
                    colour=Color.blue()
                )
            )

        # No category End.
        
        
        """
        NSFW commands:
        """
        @command(help='r/boobs')
        @commands.is_nsfw()
        async def boobs(ctx, limit:int=1):
            await self.client.reddit(ctx, 'boobs', limit)


        @command(help='r/ass')
        @commands.is_nsfw()
        async def ass(ctx, limit:int=1):
            await self.client.reddit(ctx, 'ass', limit)

        # NSFW End.


        """
        Reddit commands
        """

        @command(name='r/', help='Get post from reddit.', category='REDDIT')
        async def r(ctx, subreddit:str, limit:int=1):
            await self.client.reddit(ctx, subreddit, limit)

        # Reddit End.


        """
        Owner commands
        """

        @command()
        @commands.is_owner()
        async def test(ctx, *args, **kwargs):
            try:
                rmsg = await reference(ctx.message)
            except reference.NoneReference as e:
                await ctx.message.reply(e)
            else:
                await rmsg.reply('yuppp')

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


    

























"""


        @command(help='The bots latency')
        async def ping(ctx):
            await ctx.message.reply(embed=discord.Embed(description="**%i**ms" % round(client.latency * 1000), colour=Color.blue()))


        @command()
        @commands.has_permissions(administrator=True)
        async def test(ctx):
            print('testing test')


        @command(help='r/boobs')
        @commands.is_nsfw()
        async def boobs(ctx, limit:int=1):
            await ctx.send("BOOBS!")


        @command(help='r/ass')
        @commands.is_nsfw()
        async def ass(ctx, limit:int=1):
            await ctx.semd('ass!')



        @command()
        @commands.is_owner()
        async def enable(ctx, *channels):
            channels = await self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).enable())
            else:
                await ctx.send('\n'.join(reply))


        @command()
        @commands.is_owner()
        async def disable(ctx, *channels):
            channels = await self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).disable())
            else:
                await ctx.send('\n'.join(reply))


        @command()
        @commands.is_owner()
        async def listd(ctx):
            reply = []
            with Data.R('config') as config:
                for ch_id in config['disabled_channels']:
                    reply.append(client.get_channel(ch_id).mention)
            
            await ctx.send('\n'.join(reply))


        @command()
        @commands.is_owner()
        async def set_prefix(ctx, new_prefix):
            with Data.RW('config') as config:
                config['prefixes'][str(ctx.guild.id)] = new_prefix


        @command(aliases=['sat'])
        @commands.is_owner()
        async def server_add_tc(ctx, channel:discord.TextChannel, cname:str):
            server = Server(ctx.guild)
            server.add_text_channel(channel, cname)
            
            await client.command_success(ctx.message)
            
        
    async def get_channels_from_tuple(self, *channels):
        _channels = []
        for channel in channels:
            if channel.startswith('<#') and channel.endswith('>'):
                _channels.append(self.client.get_channel(int(channel[2:-1])))
            else:
                raise Exception("%s is not a channel." % channel)
        else:
            return _channels"""