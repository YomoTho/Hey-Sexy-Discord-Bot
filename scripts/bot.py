from typing import Union
import discord
import asyncpraw
import os
import random
import pytz
import asyncio
import inspect
import aioconsole
import re
import signal
from discord import Colour
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
try:
    from scripts.data import Data, MyChannel, Server, TimeStats
    from scripts.leveling_system import Leveling_System
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Server, TimeStats
    from leveling_system import Leveling_System



class ConsoleCommand:
    def __init__(self) -> None:
        self.all_console_commands = {}


    async def command_line(self, cmd_line: str) -> None:
        if cmd_line:
            cmd, args = cmd_line.split(' ')[0], tuple(cmd_line.split(' ')[1:])

            await self.all_console_commands[cmd](*args)


    def command(self, *args, **kwargs):
        print(args, kwargs)
        def wrapper(func):
            self.all_console_commands[kwargs.get('name') or func.__name__] = func
        
        return wrapper



class Reddit:
    def __init__(self) -> None:
        self.loggend_in = False
        load_dotenv()
        try:
            self.reddit = asyncpraw.Reddit(
                client_id=os.getenv('CLIENT_ID'), 
                client_secret=os.getenv('CLIENT_SECRET'), 
                username=os.getenv('USERNAME'), 
                password=os.getenv('PASSWORD'), 
                user_agent="NO"
            )
            self.reddit_json = Data.reddit(True)
            self.nsfw_subreddit = self.reddit_json.load()

            self.loggend_in = True
        except Exception as e:
            self.loggend_in = False
            print(e)

    async def __call__(self, ctx, sub_reddit:str, loop:int=1):
        if not self.loggend_in:
            return print("Didn't logged in reddit.")

        try:
            self.nsfw_subreddit = self.reddit_json.load()

            loop = int(loop)
            if loop > 100:
                return await ctx.send("The loop must be less than 100!")
            if not ctx.channel.is_nsfw():
                if sub_reddit in self.nsfw_subreddit['nsfw']:
                    return await ctx.send("This is not a NSFW text channel.")

            if 'gay' in sub_reddit:
                if not 'gay' in ctx.channel.name:
                    return await ctx.send('Not gay channel')

            limit = (loop * 10) if loop > 10 else 50
            self.subreddit = await self.reddit.subreddit(sub_reddit)

            self.all_post = []

            loading_msg = await ctx.reply("Loading... Might take a sec")
            async for submission in self.subreddit.top(limit=limit):
                self.all_post.append(submission)
            else:
                await loading_msg.delete()
                
                if self.all_post[0].over_18:
                    if not sub_reddit in self.nsfw_subreddit['nsfw']:
                        self.nsfw_subreddit['nsfw'].append(sub_reddit)
                        self.reddit_json.dump(self.nsfw_subreddit)
                    if not ctx.channel.is_nsfw():
                        return await ctx.send("This is not a NSFW text channel.")
                
                for i in range(loop):
                    subm = random.choice(self.all_post)
                    self.all_post.remove(subm)
                    
                    url, title = subm.url, subm.title
                
                    video_url = url

                    if video_url.endswith('.mp4'):
                        asyncio.create_task(ctx.send(f"**{title}**\n{i + 1}/{loop}: {video_url}"))
                    elif video_url[-4] == '.':
                        embed = discord.Embed(title=title)
                        embed.set_image(url=video_url)
                        embed.set_footer(text=f'{i + 1}/{loop}')
                        asyncio.create_task(ctx.send(embed=embed))
                    else:
                        asyncio.create_task(ctx.send(f"**{title}**\n{i + 1}/{loop}: {url}"))
        except Exception as e:
            if str(e) == 'Redirect to /subreddits/search':
                await ctx.send("Sub Reddit not found.")
            else:
                await ctx.message.reply(str(e))



class CBF:
    """
    CBF: Custom Bot Functions
    """
    def __init__(self) -> None:
        pass


    def load_commands(self, *command_classes) -> None:
        """
        `command_classes` is a tuple of classes -
        inside each class in `command_classes` inside the __init__ -
        there's functions in the __init__ that's decorated `@self.command()` -
        so it will "load" each command inside the __init__
        """
        for cmd_cls in command_classes:
            cmd_cls(self)


    async def command_failed(self, message:discord.Message) -> None:
        await message.add_reaction('❌')

    
    async def command_success(self, message:discord.Message) -> None:
        await message.add_reaction('✅')


    def load_categories(self) -> None:
        """
        I made my own categories var -
        So it loop for each command in self.walk_commands -
        And check it's category & permissions -
        then but it in the self.category
        """
        for command in self.walk_commands():
            _kwargs = vars(command)['__original_kwargs__']
            category = _kwargs.get('category')
            help = _kwargs.get('help')
                
            command_args = ' '.join(['<%s>' % arg for arg in list(vars(command)['params'])[1:]])
                
            if category is None:
                checks = vars(command)['checks']

                if len(checks) == 0:
                    self.categories['MISC'][str(command)] = {'help': help, 'args': command_args}

                for check in checks:
                    if 'is_owner' in str(check):
                        self.categories['OWNER'][str(command)] = {'help': help, 'args': command_args}
                    elif 'is_nsfw' in str(check):
                        self.categories['NSFW'][str(command)] = {'help': help, 'args': command_args}
                    elif 'has_permissions' in str(check):
                        self.categories['ADMIN'][str(command)] = {'help': help, 'args': command_args}
            else:
                if not category in self.categories:
                    self.categories[category] = {}

                self.categories[category][str(command)] = {'help': help, 'args': command_args}


    def message_for_reddit(self, message_content:str):
        """
        This is for the 'r/' command
        Just making r/ <subreddit> one word, for example: "r/ memes" -> "r/memes"
        """

        if message_content.startswith('r/'):
            content = message_content.split(' ')
            limit = None
            if len(content) > 2:
                limit = content[:-1]

            content = ''.join(content[:1]) + limit or ''

            message_content = content

        return message_content


    def get_stats(self, td_date) -> dict:
        embed = discord.Embed(title=td_date, colour=Colour.purple())
        embed.set_author(name=self.server.name, icon_url=self.server.icon_url)
        embed.set_thumbnail(url=self.server.icon_url)

        with Data.R('server_stats.json') as stats_data:
            today_stats = stats_data[td_date]
            total_messages = today_stats['total_messages']
            member_joins = today_stats['member_joins']
            member_leaves = today_stats['member_leaves']

        embed.add_field(name="Joins/Leaves:", value='Joins: **%i**\nLeaves: **%i**' % (member_joins, member_leaves), inline=False)
        embed.add_field(name="Messages:", value="Total messages: **%i**" % (total_messages))
        embed.set_author(name=self.server.name, icon_url=self.server.icon_url) 
        embed.set_image(url='attachment://%s' % self.server.stats_filename)
        embed.set_footer(text='Members count: %i' % len(self.server.guild.members))

        file = self.server.get_server_stats()

        return {'file': file, 'embed': embed}


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

    
    def set_iq(self, member: discord.Member, iq: int):
        with Data.RW('iq_scores.json') as iq_list:
            iq_list[str(member.id)] = iq


    def get_gay_test(self):
        says = random.choice(['**100%** GAY!', 'yea kinda gay', 'nope! **100%** straight', '**69%** gay'])

        rand_say = f'**{random.randint(0, 100)}**% gay'

        say = random.choice([rand_say, says])

        return say


    def check_if_reaction_role_message(self, message_id:str):
        messages = Data.read('reactions.json')

        if message_id in messages:
            del messages[message_id]

            if int(message_id) in self.reactions_command:
                del self.reactions_command[int(message_id)]
            if int(message_id) in self.reactions_command_remove:
                del self.reactions_command_remove[int(message_id)]

            Data('reactions.json').dump(messages)


    def channels(self, name:str):
        result = Data.read('ids.json')
        result = result['channels'][name]
        return result


    def get_msgs(self, name:str):
        result = Data.read('ids.json')
        result = result['msgs'][name]
        return result


    # return self.get_channel(self.channels(''))
    def get_system_messages_channel(self):
        return self.get_channel(self.channels('system_messages_channel'))

    
    def get_audit_log_channel(self):
        return self.get_channel(self.channels('audit_log_channel'))

    
    def get_bot_raised_error_channel(self):
        return self.get_channel(self.channels('bot_raised_error_channel'))


    def get_server_announcement_channel(self):
        return self.get_channel(self.channels('server_announcement_channel'))


    def get_server_stats_channel(self):
        return self.get_channel(self.channels('server_stats_channel'))


    def get_level_ups_channel(self):
        return self.get_channel(self.channels('level_ups_channel'))


    def get_questions_channel(self):
        return self.get_channel(self.channels('questions_channel'))


    def get_member_leave_channel(self):
        return self.get_channel(self.channels('member_leave_channel'))


    def get_roles_channel(self):
        return self.get_channel(self.channels('roles_channel'))


    def get_rules_channel(self):
        return self.get_channel(self.channels('rules_channel'))


    def get_music_commands_channel(self):
        return self.get_channel(self.channels('music_commands_channel'))


    def get_mod_room_channel(self):
        return self.get_channel(self.channels('mod_room_channel'))


    def get_admin_room_channel(self):
        return self.get_channel(self.channels('admin_room_channel'))


    def get_bot_lab_channel(self):
        return self.get_channel(self.channels('bot_lab_channel'))


    def get_shop_channel(self):
        return self.get_channel(self.channels('shop_channel'))


    def get_rules_msg(self):
        return self.get_msgs('rules_msg')


    def get_role_buy_msg(self):
        return self.get_msgs('role_buy_msg')

    
    def get_bump_channel(self):
        return self.get_channel(self.channels('bump_channel'))


    def get_staff_room_channel(self):
        return self.get_channel(self.channels('staff_room'))


    async def commet_lines(self, message_content):
        return '\n'.join(['> %s' % line for line in message_content.split('\n')])



class Bot(commands.Bot, CBF):
    def __init__(self, command_prefix, args:tuple, **options):
        super().__init__(command_prefix, intents=discord.Intents().all(), **options)
        self.categories = {'OWNER': {}, 'NSFW': {}, 'MISC': {}, 'ADMIN': {}}
        self.reddit = Reddit()
        self.prefix = None
        self.sa_timezone = pytz.timezone('Africa/Johannesburg')
        self.server_stats = TimeStats(self.sa_timezone)
        self.command_line = ConsoleCommand()
        self.server = None
        self.args = args
        self.ttt_running = list()
        self.last_deleted_message = dict()
        self.reactions_command = {}
        self.reactions_command_remove = {}
        self.do_stats = Data.read('config.json')['stats']
        self._8ball_says = ['no.', 'no???', 'Hell NO!', 'Bruh, you know its a NO', 'yes.', 'Yes??', 'ok, yea', 'Ugg, yes...', 'Tbh, no.', 'Tbh, yes', 'can you not', "ask again later when I'm less busy with ur daddy", 'sure, why not', "heck off, you know that's a no"]
        self.pfp_says = ['Cool', "Damn, that's one ugly pfp you have there", None, 'The best pfp!', None, None, None, None, None, "WTF is this??", "????", 'Who this?', 'Hmmmm, wtf??!']

        reactions_data = Data.read('reactions.json')
        if not len(reactions_data) == 0:
            self.reactions_command = {int(message_id): self.on_role_react_add for message_id in reactions_data}
            self.reactions_command_remove = {int(message_id): self.on_role_react_remove for message_id in reactions_data}

        self.rules_msg = self.get_rules_msg()
        self.buy_role_msg = self.get_role_buy_msg()
        if not self.rules_msg is None:
            self.reactions_command[self.rules_msg] = self.on_rules_react

        self.system_messages_channel = None
        self.audit_log_channel = None
        self.bot_raised_error_channel = None
        self.server_announcement_channel = None
        self.server_stats_channel = None
        self.level_ups_channel = None
        self.questions_channel = None
        self.member_leave_channel = None
        self.roles_channel = None
        self.rules_channel = None
        self.music_commands_channel = None
        self.mod_room_channel = None
        self.admin_room_channel = None
        self.bot_lab_channel = None
        self.shop_channel = None
        self.bump_channel = None
        self.staff_room_channel = None

        with Data.R('ids.json') as roles_id:
            roles_id = roles_id['roles']

            self.female_role_id = roles_id['female_role']
            self.male_role_id = roles_id['male_role']
            self.transgender_role_id = roles_id['transgender_role']
            self.reddit_role_id = roles_id['reddit_role']
            self.nsfw_pp_role_id = roles_id['nsfw++_role']
            self.anime_role_id = roles_id['anime_role']
            self.staff_role_id = roles_id['staff_role']
            self.human_role_id = roles_id['human_role']


        self.command_line.command(name='ls')(self.list_channels)
        self.command_line.command(name='cd')(self.change_channel)
        self.command_line.command(name='send')(self.channel_send)
        self.command_line.command(name='google')(self._google)
        self.command_line.command(name='eval')(self._eval)


    async def _eval(self, *string):
        string = ' '.join(string)

        await self.current_channel.send("%s = %s" % (string, eval(string)))


    async def list_channels(self):
        for channel in self.server.guild.channels:
            await aioconsole.aprint(channel.name)


    async def change_channel(self, channel_name: str):
        for channel in self.server.guild.channels:
            if channel_name.lower() in channel.name:
                self.current_channel = channel


    async def _google(self, *search):
        command = self.all_commands['google'].callback

        search = ' '.join(search)

        await command(self.current_channel, google_search=search)


    async def channel_send(self, *message):
        message = ' '.join(message)

        await self.current_channel.send(message)


    @staticmethod
    async def get_prefix(message=None) -> str:
        with Data.R('config') as config:
            prefix = config['prefix']
        
        return prefix


    def run(self, **kwargs):
        load_dotenv()
        return super().run(os.getenv('TOKEN'), **kwargs)


    def random_colour(self) -> discord.Colour:
        return discord.Colour.from_rgb(
            *[
                random.randint(0, 255) for _ in range(3)
            ]
        )

    
    # event
    async def on_ready(self):
        self.load_categories()
        self.prefix = await self.get_prefix()
        self.server = Server(self)        
        self.audit_log_channel = self.server.get_channel(cname='al')
        self.load_channels()
        self.current_channel = self.get_channel(818574185088548904)
        
        try:
            self.buy_role_msg = await self.shop_channel.fetch_message(self.buy_role_msg)
        except Exception as e:
            print(e)

        if not self.args == ():
            try:
                channel = self.get_channel(int(self.args[0]))
                await channel.send("Back online!")
            except AttributeError:
                pass

        print(self.user, 'is online.')

        self.on_ready_time = datetime.now()

        asyncio.create_task(self.console())


    def load_channels(self) -> None:
        """
        This is for the bot to have easy access to this text channels:
        """
        
        self.system_messages_channel = self.get_system_messages_channel()
        self.audit_log_channel = self.get_audit_log_channel()
        self.bot_raised_error_channel = self.get_bot_raised_error_channel()
        self.server_announcement_channel = self.get_server_announcement_channel()
        self.server_stats_channel = self.get_server_stats_channel()
        self.level_ups_channel = self.get_level_ups_channel()
        self.questions_channel = self.get_questions_channel()
        self.member_leave_channel = self.get_member_leave_channel()
        self.roles_channel = self.get_roles_channel()
        self.rules_channel = self.get_rules_channel()
        self.music_commands_channel = self.get_music_commands_channel()
        self.mod_room_channel = self.get_mod_room_channel()
        self.admin_room_channel = self.get_admin_room_channel()
        self.bot_lab_channel = self.get_bot_lab_channel()
        self.shop_channel = self.get_shop_channel()
        self.bump_channel = self.get_bump_channel()
        self.staff_room_channel = self.get_staff_room_channel()


    async def remind_to_bump(self):
        """
        Every 2 hours it will send a message in self.bump_channel
        Messgage: Bump!
        """

        hrs_to_send = [00, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

        while True:
            current_time = datetime.now().astimezone(self.sa_timezone)
            current_hour = current_time.hour

            if current_hour in [22, 23]:
                next_hour = 00
            elif (current_hour + 1) in hrs_to_send:
                next_hour = current_hour + 1
            elif (current_hour + 2) in hrs_to_send:
                next_hour = current_hour + 2

            # This will be the next time when the bot will send message
            next_time = current_time.replace(hour=next_hour, minute=00)

            wait_time = (next_time - current_time).seconds

            print("remind_to_bump: %im" % (wait_time / 60))

            await asyncio.sleep(wait_time)

            await self.bump_channel.send("Bump!")

        print("Done remind_to_bump")


    # event
    async def on_message(self, message: discord.Message) -> None:
        """print(self.all_cmd_commands)
        1:  First it checks if the message.channel == self.shop_channel -
        if so, delete the message after 69 seconds 

        2: Then it will add exp to member - Leveling_System

        3: Then checks if member is a bot, if so return out of this function

        4: Then it try if the message is math, if so call the math command

        5: checks if the message is in a DM channel, if so call on_dm_message, else -
        if do_stats is True, then add 1 to 'totday_total_messages' 

        6: Then if checks if the message.content starts with ";r/", then modify the string a bit

        7: Then process commands.
        """

        if message.author.id == 813888951818780783:
            print(message.author, message.content)
            return


        # 1
        if message.channel == self.shop_channel:
            if not message.content.startswith('- '):
                await message.delete(delay=60)
        
        # 2
        asyncio.create_task(Leveling_System.from_message(self, message)) # Adding exp to message's author

        # 3
        if message.author.bot: return

        # 4
        # math_command = self.all_commands['math'].callback
        # try:
        #     await math_command(message, sum=message.content)
        # except Exception:
        #     pass

        # 5
        if isinstance(message.channel, discord.DMChannel):
            await self.on_dm_message(message)
        else:
            if self.do_stats is True:
                self.server_stats.on_message()

            # 6
            if message.content.startswith('%sr/' % await self.get_prefix()): # This is for the reddit command
                _content = message.content.split('/')
                _content[0] = ''.join([_content[0], '/'])
                message.content = ' '.join(_content)

            # 7
            await self.process_commands(message)



    # event
    async def on_message_delete(self, message: discord.Message):
        self.check_if_reaction_role_message(str(message.id))

        channel = MyChannel(self.audit_log_channel)
        
        self.last_deleted_message[message.channel.id] = {}
        current_time = str(datetime.now(self.sa_timezone).strftime('%H:%M'))

        if message.content == '' and len(message.embeds) != 0:
            await channel.send("**%s** embed was deleted in %s\nEmbed:" % (message.author, message.channel.mention), embed=message.embeds[0])
            self.last_deleted_message[message.channel.id]['content'] = "%s\n\nTile: **%s**\nDescription: %s" % (str(message.embeds), message.embeds[0].title, message.embeds[0].description)
        else:
            embed = discord.Embed(
                description="**%s**'s message deleted in %s\n" % (message.author.mention, message.channel.mention),
                colour=discord.Color.from_rgb(255, 0, 0)
            )
            embed.add_field(name='Message:', value=message.content, inline=False)
            if int(current_time.split(':')[0]) > 12:
                current_time = '%i:%i %s' % (int(current_time.split(':')[0]) - 12, int(current_time.split(':')[1]), 'PM')
            else:
                current_time = '%s %s' % (current_time, 'AM')

            embed.set_footer(text=current_time)

            await channel.send(embed=embed)
            
            self.last_deleted_message[message.channel.id]['content'] = message.content
        
        self.last_deleted_message[message.channel.id]['user'] = message.author.id
        self.last_deleted_message[message.channel.id]['time'] = current_time


    async def on_error(self, event_method, *args, **kwargs):
        await self.server.owner.send(f"**Error!**\n{event_method}\n{args}\n{kwargs}")

        return await super().on_error(event_method, *args, **kwargs)


    # event
    async def on_command_error(self, ctx: commands.Context, exception: BaseException):
        error = str(exception)
        
        if isinstance(exception, discord.ext.commands.errors.MissingRequiredArgument):
            help_command = self.all_commands['help']._callback

            asyncio.create_task(help_command(ctx, str(ctx.command)))
        elif isinstance(exception, discord.ext.commands.errors.MissingRole):
            role = discord.utils.get(ctx.guild.roles, id=int(str(exception).split(' ')[1]))

            return await ctx.reply(embed=discord.Embed(
                description=error.replace(str(role.id), role.mention),
                colour=colour.Color.from_rgb(255, 0, 0)
            ).set_footer(
                text="Look in %s, maybe you can buy it there." % self.shop_channel
            ))
        elif isinstance(exception, discord.ext.commands.CommandNotFound):
            error = 'Command **%s** not found.' % str(ctx.message.content).replace(self.prefix, '')


        with Data.errors(write=True) as errors:
            if not 'errors' in errors:
                errors['errors'] = {}

            errors['errors'][str(ctx.message.id)] = {}
            errors['errors'][str(ctx.message.id)]['error'] = error
            errors['errors'][str(ctx.message.id)]['type'] = type(exception).__name__

            if not 'do_not_raise' in errors:
                errors['do_not_raise'] = []

        self.reactions_command[ctx.message.id] = self.on_command_error_reaction

        await self.command_failed(ctx.message)

        if not str(type(exception)) in errors['do_not_raise']:
            raise exception


    # event
    async def on_member_join(self, member: discord.Member):
        self.server_stats.member_join()

        rules_channel = self.rules_channel
        if member.bot:
            await member.add_roles(discord.utils.get(self.server.guild.roles, id=820084294361415691)) # This ID is Bots role

        embed = discord.Embed(
            title='New member!',
            description=f"Welcome **{member.name}**, to **{self.server.name}**!\n\nThe rules: {rules_channel.mention}\nAny help, ask/DM {self.server.owner.mention}\n\nThank you for joining :heart:",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name='Info:', value='IQ: **%i**\nGay: %s' % (self.get_iq(member), self.get_gay_test()), inline=False)
        
        channel = MyChannel(self.server.get_channel(cname='wj'))
        await channel.send(member.mention, embed=embed)

        Leveling_System(str(member.id), 0) # Adding the new member to levels.json

        if member.bot:
            return

        await asyncio.sleep(120) # Waiting for 2 minutes and still didn't react in rules, then send message

        try:
            if not self.human_role_id in [role.id for role in member.roles]:
                _rules_msg = await rules_channel.fetch_message(self.rules_msg)

                embed_2 = discord.Embed(title='Welcome to %s' % self.server.name, description='**To have more access to the server, react in %s**' % rules_channel.mention, colour=discord.Color.from_rgb(0, 255, 0), url=_rules_msg.jump_url)
                embed_2.set_thumbnail(url=self.server.icon_url)
                embed_2.set_footer(text='Owner: %s' % self.server.owner, icon_url=self.server.owner.avatar_url)

                await member.send(embed=embed_2)
            else:
                print(member, 'already reacted.')
        except Exception as e:
            await self.server.owner.send("Error in on_member_join: **%s**" % e)


    # event
    async def on_member_remove(self, member):
        self.server_stats.member_leave()

        self.delete_member_iq(member)

        print(f"{member} has left the server.")
        
        embed = discord.Embed(description=f'**{member.mention}** left **{self.server.name}**.', colour=discord.Color.from_rgb(255, 0, 0))
        embed.set_author(name=member, icon_url=member.avatar_url)
        
        asyncio.create_task(MyChannel(self.server.get_channel(cname='ntl')).send(embed=embed))

        member_levels = Leveling_System(str(member.id), 0)
        member_levels.remove_member() # Removing the member from levels.json


    # event
    async def on_raw_reaction_add(self, payload : discord.RawReactionActionEvent):
        if self.get_user(payload.user_id).bot is True: # This checking if the user is a bot, if so return.
            return

        if payload.message_id in self.reactions_command:
            delete = await self.reactions_command[payload.message_id](payload)
            
            if delete is True:
                del self.reactions_command[payload.message_id]
        elif payload.channel_id in self.reactions_command:
            delete = await self.reactions_command[payload.message_id](payload)
            
            if delete is True:
                del self.reactions_command[payload.channel_id]


    # event
    async def on_raw_reaction_remove(self, payload:discord.RawReactionActionEvent):
        if self.get_user(payload.user_id).bot is True: # This checking if the user is a bot, if so return.
            return
        
        if payload.message_id in self.reactions_command_remove:
            delete = await self.reactions_command_remove[payload.message_id](payload)

            if delete is True:
                del self.reactions_command_remove[payload.message_id]
        elif payload.channel_id in self.reactions_command_remove:
            delete = await self.reactions_command_remove[payload.channel_id](payload)

            if delete is True:
                del self.reactions_command_remove[payload.channel_id]

        
        """
        if not payload.user_id == client.user.id:
            if payload.channel_id == data.get_useful_channel(cname='r').id:
                with open('%sreactions.json' % data_folder) as f:
                    messages = json.load(f)

                if str(payload.message_id) in messages:
                    if str(payload.emoji) in messages[str(payload.message_id)]:
                        role_id = messages[str(payload.message_id)][str(payload.emoji)]
                        role = discord.utils.get(client.get_guild(payload.guild_id).roles, id=int(role_id))
                        user = discord.utils.get(client.get_guild(payload.guild_id).members, id=payload.user_id)
                        await user.remove_roles(role)
                else:
                    pass
        """


    # event
    async def on_message_edit(self, before:discord.Message, after:discord.Message):
        if (before.content == after.content) or (after.id in [ttt.game_msg.id for ttt in self.ttt_running]):
            return

        channel = MyChannel(self.audit_log_channel)

        embed = discord.Embed(title='Message edit:', description="In %s" % after.channel.mention, colour=discord.Color.blue())
        embed.set_author(name=after.author, url=after.jump_url, icon_url=after.author.avatar_url)
        embed.add_field(name="Before:", value=await self.commet_lines(before.content), inline=False)
        embed.add_field(name="After:", value=await self.commet_lines(after.content), inline=False)

        asyncio.create_task(channel.send(embed=embed))


    # event
    async def on_private_channel_delete(self, channel):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(a_channel.send(embed=await self.channel_delete_embed(channel)))


    # event
    async def on_private_channel_create(self, channel: discord.DMChannel):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(
            a_channel.send(
                embed=discord.Embed(
                    title='on_private_channel_create',
                    description='Channel recipient: **%s**' % channel.recipient
                )
            )
        )


    # event
    async def on_guild_channel_delete(self, channel):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(a_channel.send(embed=await self.channel_delete_embed(channel)))


    # event
    async def on_guild_channel_create(self, channel):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(a_channel.send(embed=await self.channel_create_embed(channel)))


    # event
    async def on_member_update(self, before, after):
        a_channel = MyChannel(self.audit_log_channel)

        embed = discord.Embed(colour=discord.Color.blue())
        embed.set_author(name=after, icon_url=after.avatar_url)

        if before.nick != after.nick:
            embed.add_field(name='Nickname change:', value="%s -> **%s**" % (before.nick, after.nick), inline=False)
        
        if before.roles != after.roles:
            len_before, len_after = len(before.roles), len(after.roles)
            if len_after > len_before:
                added_thing = [i.mention for i in after.roles if not i in before.roles]
                value = "Added: %s" % ' '.join(added_thing)
            elif len_after < len_before:
                removed_thing = [i.mention for i in before.roles if not i in after.roles]
                value = "Removed: %s" % ' '.join(removed_thing)
            else:
                value = 'Huh'

            embed.add_field(name='Role change:', value=value, inline=False)
        
        if before.pending != after.pending:
            embed.add_field(name='Pending change:', value="%s -> **%s**" % (before.pending, after.pending), inline=False)

        if len(embed.fields) == 0:
            return

        await a_channel.send(embed=embed)


    # event
    async def on_user_update(self, before, after):
        a_channel = MyChannel(self.audit_log_channel)

        embed = discord.Embed(colour=discord.Color.blue())
        embed.set_author(name=after, icon_url=after.avatar_url)

        if before.avatar != after.avatar:
            embed.description = "**Avatar change:**"
            embed.add_field(name='Old avatar:', value=before.avatar_url, inline=False)
            embed.add_field(name='New avatar:', value=after.avatar_url, inline=False)
        
        if before.name != after.name:
            embed.add_field(name='Username change:', value="%s -> **%s**" % (before.username, after.avusernameatar), inline=False)
        
        if before.discriminator != after.discriminator:
            embed.add_field(name='Discriminator change:', value="%s -> **%s**" % (before.discriminator, after.discriminator), inline=False)

        if len(embed.fields) == 0:
            return

        await a_channel.send(embed=embed)


    # event
    async def on_guild_update(self, before, after):
        a_channel = MyChannel(self.audit_log_channel)

        changes = await self.get_changes(before, after)

        embed = discord.Embed(title="Server update:", description=after, colour=discord.Color.blue())
        embed.set_thumbnail(url=after.icon_url)

        if 'features' in changes:
            del changes['features']

        for name, val in changes.items():
            if type(val[1]) in [list, tuple]:
                len_before, len_after = len(val[0]), len(val[1])
                if len_after > len_before:
                    added_thing = [i for i in val[1] if not i in val[0]]
                    value = "Added: %s" % ' '.join(added_thing)
                elif len_after < len_before:
                    removed_thing = [i for i in val[0] if not i in val[1]]
                    value = "Removed: %s" % ' '.join(removed_thing)
                else:
                    value = str(val)
            else:
                value = '%s -> **%s**' % (val[0], val[1])
            
            embed.add_field(name=name, value=value, inline=False)

        asyncio.create_task(a_channel.send(embed=embed))


    # event
    async def on_guild_role_create(self, role):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(a_channel.send(embed=await self.role_create_embed(role)))


    # event
    async def on_guild_role_delete(self, role):
        a_channel = MyChannel(self.audit_log_channel)

        asyncio.create_task(a_channel.send(embed=await self.role_delete_embed(role)))


    # event
    async def on_guild_role_update(self, before, after):
        a_channel = MyChannel(self.audit_log_channel)

        changes = await self.get_changes(before, after) 

        embed = discord.Embed(title="Role update:", description=after.mention, colour=discord.Color.blue())

        if 'tags' in changes:
            del changes['tags']

        if 'color' in changes:
            del changes['color']

        if 'position' in changes:
            del changes['position']

        if len(changes) == 0:
            return

        for name, val in changes.items():
            if type(val[1]) in [list, tuple]:
                len_before, len_after = len(val[0]), len(val[1])
                if len_after > len_before:
                    added_thing = [i for i in val[1] if not i in val[0]]
                    value = "Added: %s" % ' '.join(added_thing)
                elif len_after < len_before:
                    removed_thing = [i for i in val[0] if not i in val[1]]
                    value = "Removed: %s" % ' '.join(removed_thing)
                else:
                    value = str(val)
            else:
                value = '%s -> **%s**' % (val[0], val[1])
            
            embed.add_field(name=name, value=value, inline=False)

        if len(embed.fields) == 0:
            return

        asyncio.create_task(a_channel.send(embed=embed))


    # event
    async def on_guild_channel_update(self, before, after):
        a_channel = MyChannel(self.audit_log_channel)
        list_before = inspect.getmembers(before)
        list_after = inspect.getmembers(after)

        changes = await self.get_changes(before, after)

        embed = discord.Embed(title="Channel update:", description=after.mention, colour=discord.Color.blue())

        if "members" in changes and "changed_roles" in changes:
            del changes["members"]
        
        if 'overwrites' in changes:
            del changes['overwrites']

        if 'position' in changes:
            del changes['position']

        for name, val in changes.items():
            if type(val[1]) in [list, tuple]:
                len_before, len_after = len(val[0]), len(val[1])
                if len_after > len_before:
                    added_thing = [i.mention for i in val[1] if not i in val[0]]
                    value = "Added: %s" % ' '.join(added_thing)
                elif len_after < len_before:
                    removed_thing = [i.mention for i in val[0] if not i in val[1]]
                    value = "Removed: %s" % ' '.join(removed_thing)
                else:
                    value = 'Huh'
            else:
                value = '%s -> **%s**' % (val[0], val[1])
            
            embed.add_field(name=name, value=value, inline=False)

        if not len(embed.fields) == 0:
            asyncio.create_task(a_channel.send(embed=embed))


    # event
    async def on_member_ban(self, guild, user):
        sa_channel = MyChannel(self.server_announcement_channel)

        await sa_channel.send(embed=discord.Embed(title='Member banned!', description="%s is banned from **%s**" % (user.mention, guild), colour=discord.Color.from_rgb(255, 0, 0)).set_author(name=user, icon_url=user.avatar_url))


    # event
    async def on_member_unban(self, guild, user):
        sa_channel = MyChannel(self.server_announcement_channel)

        await sa_channel.send(embed=discord.Embed(title='Member unban!', description="%s is unban from **%s**" % (user.mention, guild), colour=discord.Color.from_rgb(0, 255, 0)).set_author(name=user, icon_url=user.avatar_url))


    # event
    async def on_invite_create(self, invite):
        a_channel = MyChannel(self.audit_log_channel)

        des = "**Created by:** %s\n\nmax_age: **%s**s\nmax_uses: **%s**\n\nChannel: %s\n\nUrl: %s" % (invite.inviter.mention, invite.max_age, invite.max_uses, invite.channel.mention, invite)

        await a_channel.send(embed=discord.Embed(title="Invite created", description=des, colour=discord.Color.from_rgb(0, 255, 0)))


    async def on_invite_delete(self, invite):
        a_channel = MyChannel(self.audit_log_channel)

        des = "**Channel:** %s\n\nUrl: %s" % (invite.channel.mention, invite)

        await a_channel.send(embed=discord.Embed(title="Invite deleted", description=des, colour=discord.Color.from_rgb(255, 0, 0)))


    # event
    async def on_voice_state_update(self, member, before, after):
        a_channel = MyChannel(self.audit_log_channel)

        embed = discord.Embed()
        embed.set_author(name=member, icon_url=member.avatar_url)
        
        if before.channel is None:
            des = "Joined %s" % after.channel.mention
            embed.color = discord.Color.from_rgb(0, 255, 0)
        elif after.channel is None:
            des = "Left %s" % before.channel.mention
            embed.color = discord.Color.from_rgb(255, 0, 0)
        else:
            des = "%s moved to -> %s" % (before.channel.mention, after.channel.mention)
            embed.color = discord.Color.blue()

        embed.description = des

        await a_channel.send(embed=embed)    



    async def stats(self) -> None:
        """
        Every day it will post server stats
        """

        config = Data.read('config.json')

        if not config['stats']:
            return

        await self.wait_until_ready()

        asyncio.create_task(self.remind_to_bump())

        await asyncio.sleep(1) # Just waiting for on_ready() to finnish

        server_stats_channel = MyChannel(self.server.get_channel(cname='ss'))
            
        while True:
            current_time = datetime.today().astimezone(self.sa_timezone)

            self.today_date = current_time.strftime('%Y-%m-%d')

            try:
                server_stats_alarm = current_time.replace(day=current_time.day+1, hour=00, minute=00)
            except ValueError: # It's probably the end of the month
                server_stats_alarm = current_time.replace(month=current_time.month+1, day=1, hour=00, minute=00)
            #server_stats_alarm = current_time

            wait_time = (server_stats_alarm - current_time).seconds
            
            print('Stats: %im' % (wait_time / 60))

            await asyncio.sleep(wait_time)

            await server_stats_channel.send(**self.get_stats(self.today_date))

            Data.errors().clean_erros()
            self.server_stats.update_date()
            self.server_stats.add_date()

            await asyncio.sleep(66)
 

    async def _exit(self):
        await self.reddit.reddit.close()
        await self.close()


    async def on_dm_message(self, message):
        if message.author.id == self.server.owner_id:
            await self.process_commands(message)
            return
        
        if not message.author.bot:
            content = await self.commet_lines(message.content)
            
            if len(message.embeds) != 0 and message.content.startswith('https://'):
                for embed in message.embeds:
                    url = embed.to_dict()['url']
                    embed = discord.Embed(description='%s\n﹂ %s' % (content, message.id))
                    embed.set_author(name=message.author, icon_url=message.author.avatar_url, url=message.jump_url)
                    embed.set_footer(text=message.author.id)
                    msg = await self.server.owner.send(embed=embed)
                    await msg.reply(url)
                else:
                    return

            embed = discord.Embed(description='%s\n﹂ %s' % (content, message.id), color=discord.Color.blue())
            embed.set_footer(text=message.author.id)
            embed.set_author(name=message.author, icon_url=message.author.avatar_url, url=message.jump_url)
            msg = await self.server.owner.send(embed=embed)


    async def on_command_error_reaction(self, payload:discord.RawReactionActionEvent):
        if payload.emoji.name == '❌':
            errors_data_cls = Data.errors()
            errors_data = errors_data_cls.load()

            if str(payload.message_id) in errors_data['errors']:
                error_msg = errors_data['errors'][str(payload.message_id)]['error']
                error_type = errors_data['errors'][str(payload.message_id)]['type']

                embed = self.make_error_message(error_msg)
                embed.set_footer(text=error_type)

                message = await self.get_channel(payload.channel_id).fetch_message(payload.message_id)

                await message.reply(embed=embed)

                del errors_data['errors'][str(payload.message_id)]

                errors_data_cls.dump(errors_data)
        
        return True


    async def on_rules_react(self, payload:discord.RawReactionActionEvent):
        member: discord.Member = discord.utils.get(self.get_guild(payload.guild_id).members, id=payload.user_id)
        role: discord.Role = discord.utils.get(self.get_guild(payload.guild_id).roles, id=821839747520528404) # 821839747520528404 is Sexy Human

        if not role in member.roles:
            await member.add_roles(role)
            await asyncio.sleep(random.randint(7, 20))
            channel: discord.TextChannel = self.get_channel(818547292357394453) # 818547292357394453 is general-chat
            await channel.send("Welcome %s :heart:" % member.mention)
            
            await asyncio.sleep(random.randint(30, 100))

            if len(member.roles) == 2:
                await channel.send("You can react in %s, to have more access to this server" % self.get_channel(848632564640907337).mention) # 848632564640907337 is roles channel


    async def on_role_react_add(self, payload:discord.RawReactionActionEvent):
        data = Data.read('reactions.json')[str(payload.message_id)]

        if payload.emoji.name in data:
            role_id = data[payload.emoji.name]

            member = discord.utils.get(self.server.guild.members, id=payload.user_id)
            role = discord.utils.get(self.server.guild.roles, id=role_id)

            await member.add_roles(role)


    async def channel_create_embed(self, channel) -> discord.Embed:
        channel_type = channel.type
        channel_category = channel.category

        des = "%s channel **%s** **%s** create in **%s** category" % (channel_type, channel.name, channel.mention, channel_category)

        return discord.Embed(description=des, colour=discord.Color.from_rgb(0, 255, 0))


    async def channel_delete_embed(self, channel) -> discord.Embed:
        channel_type = channel.type
        channel_category = channel.category

        des = "%s channel **%s** deleted in **%s** category" % (channel_type, channel, channel_category)

        return discord.Embed(description=des, colour=discord.Color.from_rgb(255, 0, 0))


    async def get_changes(self, before, after) -> dict:
        list_before = inspect.getmembers(before)
        list_after = inspect.getmembers(after)

        changes = {}

        for idx, attr in enumerate(list_after):
            before_attr = list_before[idx]
            if not attr[0].startswith('_') and not str(type(attr[1])) in ["<class 'method'>", "<class 'method-wrapper'>"]:
                if not attr[1] == before_attr[1]:
                    changes[attr[0]] = [before_attr[1], attr[1]]

        return changes


    async def role_create_embed(self, role) -> discord.Embed:
        des = "name: **%s**: %s" % (role, role.mention)

        return discord.Embed(title="Role created:", description=des, colour=discord.Color.from_rgb(0, 255, 0))


    async def role_delete_embed(self, role) -> discord.Embed:
        des = "name: **%s**" % role

        return discord.Embed(title="Role deleted:", description=des, colour=discord.Color.from_rgb(255, 0, 0))


    async def on_role_react_remove(self, payload:discord.RawReactionActionEvent):
        data = Data.read('reactions.json')[str(payload.message_id)]

        if payload.emoji.name in data:
            role_id = data[payload.emoji.name]
            member = self.get_user(payload.user_id)

            member = discord.utils.get(self.server.guild.members, id=payload.user_id)
            role = discord.utils.get(self.server.guild.roles, id=role_id)

            await member.remove_roles(role)


    def make_error_message(self, error_msg, url='') -> discord.Embed:
        return discord.Embed(
            title=':x: Error:',
            description='> ' + error_msg,
            url=url,
            colour=discord.Color.from_rgb(255, 0, 0)
        )


    def delete_member_iq(self, member:discord.Member):
        """
        Delete's the user's ID & IQ in iq_scores.json
        """
        with Data.RW('iq_scores.json') as data:
            try:
                del data[str(member.id)]
            except KeyError as e:
                print("%s  %s has no IQ" % (member, e))


    async def console(self):
        while True:
            full_cmd = await aioconsole.ainput("%s: " % self.current_channel.name)

            try:
                await self.command_line.command_line(full_cmd)
            except KeyError as e:
                print("Error", e)