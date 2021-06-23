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
    from scripts.data import Data, MyChannel, Server
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Server



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




class Bot(commands.Bot, CBF):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.categories = {'OWNER': {}, 'NSFW': {}, 'NC': {}, 'ADMIN': {}}
        self.reddit = Reddit()
        self.prefix = None
        self.sa_timezone = pytz.timezone('Africa/Johannesburg')
        self.server = None


    @staticmethod
    async def get_prefix(message=None):
        with Data.R('config') as config:
            prefix = config['prefix']
        
        return prefix


    def run(self, **kwargs):
        load_dotenv()
        return super().run(os.getenv('TOKEN'), **kwargs)

    
    async def on_ready(self):
        self.load_categories()
        self.prefix = await self.get_prefix()
        self.server = Server(self)

        print(self.user, 'is online.')


    async def on_message(self, message):
        if message.author.bot: return

        if message.content.startswith('%sr/' % await self.get_prefix()): # This is for the reddit command
            _content = message.content.split('/')
            _content[0] = ''.join([_content[0], '/'])
            message.content = ' '.join(_content)

        await self.process_commands(message)


    async def on_command_error(self, ctx, exception):
        with Data.errors(write=True) as errors:
            if not 'errors' in errors:
                errors['errors'] = {}

            errors['errors'][str(ctx.message.id)] = {}
            errors['errors'][str(ctx.message.id)]['error'] = str(exception)
            errors['errors'][str(ctx.message.id)]['type'] = str(type(exception))

            if not 'do_not_raise' in errors:
                errors['do_not_raise'] = []

        await self.command_failed(ctx.message)

        if not str(type(exception)) in errors['do_not_raise']:
            raise exception


    async def stats(self):
        """
        Every day it will post server stats
        """

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
 
