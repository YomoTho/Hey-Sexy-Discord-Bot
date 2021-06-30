import discord
import asyncpraw
import os
import random
import pytz
import asyncio
from discord import colour
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
try:
    from scripts.data import Data, MyChannel, Server, TimeStats
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Server, TimeStats



class Reddit:
    def __init__(self) -> None:
        load_dotenv()
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv('CLIENT_ID'), 
            client_secret=os.getenv('CLIENT_SECRET'), 
            username=os.getenv('USERNAME'), 
            password=os.getenv('PASSWORD'), 
            user_agent="NO"
        )
        self.reddit_json = Data.reddit(True)
        
        self.nsfw_subreddit = self.reddit_json.load()


    async def __call__(self, ctx, sub_reddit:str, loop:int=1):
        try:
            self.nsfw_subreddit = self.reddit_json.load()

            loop = int(loop)
            if loop > 100:
                return await ctx.send("The loop must be less than 100!")
            if not ctx.channel.is_nsfw():
                if sub_reddit in self.nsfw_subreddit['nsfw']:
                    return await ctx.send("This is not a NSFW text channel.")

            limit = (loop * 10) if loop > 10 else 50
            self.subreddit = await self.reddit.subreddit(sub_reddit)

            self.all_post = []

            async for submission in self.subreddit.top(limit=limit):
                self.all_post.append(submission)
            else:
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
                        await ctx.send(f"**{title}**\n{i + 1}/{loop}: {video_url}")
                    elif video_url[-4] == '.':
                        embed = discord.Embed(title=title)
                        embed.set_image(url=video_url)
                        embed.set_footer(text=f'{i + 1}/{loop}')
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"**{title}**\n{i + 1}/{loop}: {url}")
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


    def load_commands(self, *command_classes):
        for cmd_cls in command_classes:
            cmd_cls(self)


    async def command_failed(self, message:discord.Message) -> None:
        await message.add_reaction('❌')

    
    async def command_success(self, message:discord.Message) -> None:
        await message.add_reaction('✅')


    def load_categories(self):
        for command in self.walk_commands():
            _kwargs = vars(command)['__original_kwargs__']
            category = _kwargs.get('category')
            help = _kwargs.get('help')
                
            command_args = ' '.join(['<%s>' % arg for arg in list(vars(command)['params'])[1:]])
                
            if category is None:
                checks = vars(command)['checks']

                if len(checks) == 0:
                    self.categories['NC'][str(command)] = {'help': help, 'args': command_args}

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
        embed = discord.Embed(title=td_date, colour=colour.Color.purple())
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


    def get_gay_test(self):
        says = random.choice(['**100%** GAY!', 'yea kinda gay', 'nope! **100%** straight', '**69%** gay'])

        rand_say = f'**{random.randint(0, 100)}**% gay'

        say = random.choice([rand_say, says])

        return say


    def check_if_reaction_role_message(self, message_id:str):
        messages = Data.read('reactions.json')

        if message_id in messages:
            del messages[message_id]

            Data('reactions.json').dump(messages)


    def channels(self, name:str):
        result = Data.read('ids.json')
        result = result['channels'][name]
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


    async def commet_lines(self, message_content):
        return '\n'.join(['> %s' % line for line in message_content.split('\n')])



class Bot(commands.Bot, CBF):
    def __init__(self, command_prefix, args:tuple, **options):
        super().__init__(command_prefix, **options)
        self.categories = {'OWNER': {}, 'NSFW': {}, 'NC': {}, 'ADMIN': {}}
        self.reddit = Reddit()
        self.prefix = None
        self.sa_timezone = pytz.timezone('Africa/Johannesburg')
        self.server = None
        self.args = args
        self.ttt_running = list()
        self.last_deleted_message = dict()
        self.reactions_command = {823307869746495568: self.on_rules_react}
        self.reactions_command_remove = {}

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


    @staticmethod
    async def get_prefix(message=None):
        with Data.R('config') as config:
            prefix = config['prefix']
        
        return prefix


    def run(self, **kwargs):
        load_dotenv()
        return super().run(os.getenv('TOKEN'), **kwargs)

    
    # event
    async def on_ready(self):
        self.load_categories()
        self.prefix = await self.get_prefix()
        self.server = Server(self)        
        self.audit_log_channel = self.server.get_channel(cname='al')
        self.load_channels()

        if not self.args == ():
            try:
                channel = self.get_channel(int(self.args[0]))
                await channel.send("Back online!")
            except AttributeError:
                pass

        print(self.user, 'is online.')

        self.on_ready_time = datetime.now()


    def load_channels(self):
        # This is for the bot to have easy access to this text channels:
        
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


    # event
    async def on_message(self, message):
        if message.author.bot: return

        if isinstance(message.channel, discord.DMChannel):
            await self.on_dm_message(message)
        else:
            if message.content.startswith('%sr/' % await self.get_prefix()): # This is for the reddit command
                _content = message.content.split('/')
                _content[0] = ''.join([_content[0], '/'])
                message.content = ' '.join(_content)

            await self.process_commands(message)


    # event
    async def on_message_delete(self, message):
        self.check_if_reaction_role_message(str(message.id))

        channel = MyChannel(self.audit_log_channel)

        embed = discord.Embed(
            description="**%s**'s message deleted in %s\n" % (message.author.mention, message.channel.mention),
            colour=discord.Color.from_rgb(255, 0, 0)
        )
        embed.add_field(name='Message:', value=message.content, inline=False)
        current_time = str(datetime.now(self.sa_timezone).strftime('%H:%M'))
        if int(current_time.split(':')[0]) > 12:
            current_time = '%i:%i %s' % (int(current_time.split(':')[0]) - 12, int(current_time.split(':')[1]), 'PM')
        else:
            current_time = '%s %s' % (current_time, 'AM')

        embed.set_footer(text=current_time)
        
        await channel.send(embed=embed)
        
        self.last_deleted_message[message.channel.id] = {}
        self.last_deleted_message[message.channel.id]['user'] = message.author.id
        self.last_deleted_message[message.channel.id]['content'] = message.content
        self.last_deleted_message[message.channel.id]['time'] = current_time


    # event
    async def on_command_error(self, ctx, exception):
        with Data.errors(write=True) as errors:
            if not 'errors' in errors:
                errors['errors'] = {}

            errors['errors'][str(ctx.message.id)] = {}
            errors['errors'][str(ctx.message.id)]['error'] = str(exception)
            errors['errors'][str(ctx.message.id)]['type'] = str(type(exception))

            if not 'do_not_raise' in errors:
                errors['do_not_raise'] = []

        self.reactions_command[ctx.message.id] = self.on_command_error_reaction

        await self.command_failed(ctx.message)

        if not str(type(exception)) in errors['do_not_raise']:
            raise exception


    # event
    async def on_member_join(self, member):
        stats = TimeStats()
        stats.member_join()

        rules_channel = self.server.get_channel(cname='rules')
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


    # event
    async def on_member_remove(self, member):
        stats = TimeStats()
        stats.member_leave()

        self.delete_member_iq(member)

        print(f"{member} has left the server.")
        
        embed = discord.Embed(description=f'**{member.mention}** left **{self.server.name}**.', colour=discord.Color.from_rgb(255, 0, 0))
        embed.set_author(name=member, icon_url=member.avatar_url)
        
        await MyChannel(self.server.get_channel(cname='ntl')).send(embed=embed)


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


    async def stats(self):
        """
        Every day it will post server stats
        """

        config = Data.read('config.json')

        if not config['stats']:
            return

        await self.wait_until_ready()

        await asyncio.sleep(1) # Just waiting for on_ready() to finnish

        server_stats_channel = MyChannel(self.server.get_channel(cname='ss'))
            
        while self.is_closed:
            current_time = datetime.today()

            today_date = current_time.strftime('%Y-%m-%d')

            server_stats_alarm = current_time.replace(day=current_time.day+1, hour=00, minute=00)
            #server_stats_alarm = current_time

            wait_time = (server_stats_alarm - current_time).seconds

            await asyncio.sleep(wait_time)

            await server_stats_channel.send(**self.get_stats(today_date))

            Data.errors().clean_erros()

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
        user = discord.utils.get(self.get_guild(payload.guild_id).members, id=payload.user_id)
        role = discord.utils.get(self.get_guild(payload.guild_id).roles, id=821839747520528404) # 821839747520528404 is Sexy Human
        await user.add_roles(role)


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