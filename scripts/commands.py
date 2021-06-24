import discord
import os
import random
import asyncio
from discord import Color
from discord import colour
from discord.ext import commands
from games import TicTacToe
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
        async def test(ctx, member:discord.Member):
            print('web_status', member.web_status)
            print('desktop_status', member.desktop_status)
            print('is_on_mobile', member.is_on_mobile())


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


class Admin_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command()
        @self.is_admin()
        async def pin(ctx):
            try:
                rmsg = await self.reference(ctx.message)
            except Reference.NoneReference as e:
                return await ctx.send(e)
            else:
                await rmsg.pin()
    

        @self.command()
        @self.is_admin()
        async def clear(ctx, amount:int=0):
            await ctx.channel.purge(limit=amount + 1)


        @self.command()
        @self.is_admin()
        async def kick(ctx, member : discord.Member, *, reason=None):
            await member.kick(reason=reason)
            await ctx.message.add_reaction('🦶🏽')
            await ctx.send(f'**{member}** kicked!')


        @self.command()
        @self.is_admin()
        async def ban(ctx, member : discord.Member, *, reason=None):
            bans_says = ['**{}** is banned from this server.', 'Yes! That poes **{}** is banned from this server!']
            await member.ban(reason=reason)
            await ctx.message.add_reaction('✅')
            await ctx.send(random.choice(bans_says).format(member))


        @self.command()
        @self.is_admin()
        async def bans(ctx):
            banned_users = await ctx.guild.bans()
            if len(banned_users) > 0:
                embed = discord.Embed(title=f'{len(banned_users)} Banned Member(s)', color=discord.Color.from_rgb(255, 0, 0))
                for ban_usr in banned_users:
                    embed.add_field(name=f'{ban_usr.user}  [ ID: {ban_usr.user.id} ]', value=f'Reason: **{ban_usr.reason}**', inline=False)
                else:
                    await ctx.send(embed=embed)
            else:
                await ctx.send("There's nobody banned in this server.")


        @self.command()
        @self.is_admin()
        async def unban(ctx, id:int):
            user = await client.fetch_user(id)
            await ctx.guild.unban(user)
            await self.client.command_success(ctx.message)


    
    def is_admin(self):
        def wrapper(ctx):
            return ctx.author.guild_permissions.administrator
        return commands.check(wrapper)
            

    def command(self, *args, **kwargs):
        return super().command(*args, category='ADMIN', **kwargs)



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



class Fun_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='FUN', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(aliases=['ttt'], help='Tic-tac-toe game')
        async def tictactoe(ctx, player1, player2 : discord.Member=None):
            if player1 == 'bvb': # This stands for 'Bot vs Bot'
                player1 = client.get_user(816668604669755433) # This ID is local bot
                player2 = client.user
            else:
                if type(player1) is str:
                    try:
                        player1 = client.get_user(int(player1[2:-1]))
                    except ValueError:
                        player1 = client.get_user(int(player1[3:-1]))
                if player2 is None:
                    player2 = ctx.author

            if player1 == player2:
                raise Exception("Player 1 and Player 2, can't be the same.")
            
            if player1 is None: raise Exception("**Player 1 ({}) not found.**".format(player1))
            
            ttt_game = TicTacToe(player1, player2, ctx, self.client.ttt_running, client)
            self.client.ttt_running.append(ttt_game)
            ttt_game.all_running_ttt = self.client.ttt_running
            ttt_game.current_game = ttt_game
            game_msg = await ctx.send(await ttt_game.print())
            ttt_game.game_msg = game_msg

            if (player1.bot == False and player2.bot == False) or (not player1.bot or not player2.bot):
                for emoji in ttt_game.reactions:
                    await game_msg.add_reaction(emoji=emoji)

            embed = discord.Embed(description=f"**{ttt_game.turn.name}** turn")

            wtit = await ctx.send(embed=embed) # 'wtit' stands for 'whos turn is it'
            ttt_game.whos_turn_msg = wtit
            
            if ttt_game.turn.bot:
                await asyncio.sleep(2)
                await ttt_game.move(await ttt_game.smart_bot_move())
            
            if not player1.bot or not player2.bot: # This checks if a user didn't make a move for a while
                make_move_msgs = ttt_game.make_move_msgs
                wait_time = 40
                while ttt_game.running:
                    count = ttt_game.count
                    await asyncio.sleep(wait_time)
                    if count == ttt_game.count:
                        make_move_msg = await ctx.send(f'{ttt_game.turn.mention} make a move!')
                        make_move_msgs.append(make_move_msg)
                        await asyncio.sleep(wait_time)
                        if count == ttt_game.count:
                            ttt_game.running = False
                            ttt_game.all_running_ttt.remove(ttt_game.current_game)
                            done_embed = discord.Embed(description=f"**{ttt_game.turn.name}** took too long to make a move, what a NOOB!")
                            await ttt_game.whos_turn_msg.edit(embed=done_embed)
                            for msg in make_move_msgs:
                                await msg.delete()
                            break


        @self.command(help="IQ test")
        async def iqtest(ctx, member:discord.Member=None):
            member = member or ctx.author
            
            iq = self.get_iq(member, see_only=True)

            embed = discord.Embed(description='IQ: **%i**' % iq, colour=Color.blue())
            embed.set_author(name=member, icon_url=member.avatar_url)

            await ctx.send(embed=embed)


        @self.command(help="Gay test")
        async def gaytest(ctx, member:discord.Member=None):
            member = member or ctx.author

            say = self.get_gay_test()

            embed = discord.Embed(description=say, colour=Color.from_rgb(255,105,180))
            embed.set_author(name=member, icon_url=member.avatar_url)

            await ctx.send(embed=embed)


        @self.command(aliases=['g'], help='Guess between 0-6')
        async def guess(ctx, user_guess:int):
            if user_guess >= 0 and user_guess <= 6:
                bot_guess = random.randint(0, 6)
                
                embed = discord.Embed(description="I guess: **%i**\nYou guessed: **%i**"  % (bot_guess, user_guess))
                await ctx.send(embed=embed)
                if user_guess == bot_guess:
                    exp = random.choice([600, 1000, 500, 400, 1200, 4000, 10, 1, 69, 666, 777, 999])
                    #user = Leveling_System(ctx.author)
                    #leveled_up = user + exp
                    #if leveled_up[0]: # Check if user leveled up
                    #    await send_lvl_up_msg(leveled_up)
                    await ctx.send("Wow! + **%i** exp" % exp)
            else:
                await ctx.send("You must guess between 0-6")

    """
    Command functions
    """

    # iqtest command
    def get_iq(self, member:discord.Member, see_only:bool=False) -> int:
        iqscores = Data.read('iq_scores.json')

        if not see_only:
            luck = random.randint(0, 10)
            low, high = 0, 10
            if luck == 9:
                low, high = 10, 420

            if str(member.id) in iqscores:
                if luck == 9:
                    if random.randint(0, 10) != 9: low, high = 0, 10
                    iq = random.randint(low, high)
                else:
                    iq = iqscores[str(member.id)]
            else:
                iq = random.randint(low, high)

            iqscores[str(member.id)] = iq

            Data('iq_scores.json').dump(iqscores)
        else:
            iq = iqscores[str(member.id)]

        return iq


    def get_gay_test(self):
        says = random.choice(['**100%** GAY!', 'yea kinda gay', 'nope! **100%** straight', '**69%** gay'])

        rand_say = f'**{random.randint(0, 100)}**% gay'

        say = random.choice([rand_say, says])

        return say


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









