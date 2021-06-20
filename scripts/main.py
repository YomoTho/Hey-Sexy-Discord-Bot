import discord
import json
import os
import asyncio
import pytz
import requests
import sys
import insta
import shutil
import matplotlib.pyplot as plt
import inspect
from typing import Union
from Reddit_Cmd import Reddit
from timeAndDateManager import TimeStats
from datetime import datetime, time
from discord.ext import tasks, commands
from levelingSystem import Leveling_System, Money
from random import randint, choice
from games import TicTacToe
from dotenv import load_dotenv
from data import Data

    #Africa/Johannesburg

data_folder = '../data/'
print("Starting...")

with open(f'{data_folder}config.json') as f:
    d = json.load(f)
    command_prefix = d['prefix']

intents = discord.Intents().all()
client = commands.Bot(command_prefix=command_prefix, intents=intents)
client.remove_command('help')

# This class have data of the server, like server, server owner, id & Text Channels, etc

class Send_Message(Data):
    def __init__(self, channel):
        super().__init__(client)
        self.channel = channel
        self.config = self.load_config()
        
    def check(func): # This check if the channel is disabled or not, if disabled it won't call the function.
        async def in_check(self, *args, **kwargs):
            if not self.channel.id in self.config['disabled_channels']:
                await func(self, *args, **kwargs)
        return in_check
    
    def enable(self):
        if self.channel.id in self.config['disabled_channels']:
            self.config['disabled_channels'].remove(self.channel.id)
            self.save_config(self.config)
            return f"{self.channel} enabled."
        else:
            return f"{self.channel} is already not disabled."
        
    def disable(self):
        if not self.channel.id in self.config['disabled_channels']:
            self.config['disabled_channels'].append(self.channel.id)
            self.save_config(self.config)
            return f"{self.channel} disabled."
        else:
            return f"{self.channel} is already disabled."
        
    @check
    async def send(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)

    @classmethod
    def audit_log(cls):
        return cls(data.get_useful_channel('al'))


class Stats:
    def __init__(self) -> None:
        self.filename = 'stats.png'
        self.last_days = 7

    def load_stats(self) -> dict:
        return read_data_file(filename='serverDates.json')


    def get_stats(self) -> discord.File:
        stats = read_data_file('serverDates.json')

        dates, total_messgae, member_joins, member_leaves = [], [], [], []

        last_days = 7

        for stat in list(stats)[-last_days:]:
            dates.append(str(stat)[-5:])
            total_messgae.append(stats[stat]['total_messages'])
            member_joins.append(stats[stat]['member_joins'])
            member_leaves.append(stats[stat]['member_leaves'])


        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.suptitle("The Last %i days" % last_days)
        ax1.plot(dates, member_joins, label='member_joins', color='green')
        ax1.plot(dates, member_leaves, label='member_leaves', color='red')
        ax1.set_title('Member joins')
        ax1.legend()
        ax2.plot(dates, total_messgae)
        ax2.set_title('Total messages')

        fig.set_size_inches(10, 5)
        ax2.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        ax1.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        fig.savefig(self.filename)

        file = discord.File(self.filename)

        return file


class Reference:
    class NoneReference(Exception): 
        def __init__(self, description:str=None) -> None:
            super().__init__(description or "You didn't reply to a message.")

    def __init__(self, message:discord.Message) -> None:
        self.message = message
        self.reference = message.reference

        if self.reference is None:
            raise self.NoneReference()


    async def get_reference(self):
        self.channel = client.get_channel(self.reference.channel_id)

        message = await self.channel.fetch_message(self.reference.message_id)

        return message


    async def __aenter__(self):
        self.channel = client.get_channel(self.reference.channel_id)

        return await self.channel.fetch_message(self.reference.message_id)

    async def __aexit__(self, *args):
        return False


# Global variables

data = Data(client)
status_number = 0
server = None
server_owner = None
ttt_running = list()
no_no_words = ['discord.gg/']
sa_timezone = pytz.timezone('Africa/Johannesburg')
last_deleted_message = dict()
announce_message = None
mod_files = None
dm_messages = []

# Global variables ^^^
 

async def store_data():
    global server_owner, server
    server_owner = data.get_owner()
    server = data.get_server()


async def get_tday_data(time_stats=None):
    guild = client.get_guild(int(data.server_id))
    async def server_members():
        return [member for member in guild.members]
    
    
    members = await server_members()
    total_members = len(members)
    total_bots = len([_bot for _bot in members if _bot.bot])
    total_humans = len([human for human in members if not human.bot])
    total_new_joins = time_stats.get_today_member_joins()
    total_member_leaves = time_stats.get_today_member_leaves()
    total_tday_msgs = time_stats.get_today_total_messaages()
    
    stats_msg = f"""
    Total members: **{total_members}**
    Total humans: **{total_humans}**
    Total bots: **{total_bots}**
    
    Members joined: **{total_new_joins}**
    Members leaved: **{total_member_leaves}**
    Today's total message's: **{total_tday_msgs}**
    """
    return total_members, total_humans, total_bots, total_new_joins, total_member_leaves, total_tday_msgs


def return_warnings(user : discord.Member, users=False, r_count=False):
    warnings = read_data_file('warnings.json')
    if users:
        return warnings
    else:
        return len([warning for warning in warnings[str(user.id)]]) if not warnings == {} else 0


def check_if_reaction_role_message(message_id:str):
    with open('%sreactions.json' % data_folder) as f:
        messages = json.load(f)

    if message_id in messages:
        del messages[message_id]

        with open('%sreactions.json' % data_folder, 'w') as f:
            json.dump(messages, f, indent=4)


async def check_time():
    await client.wait_until_ready()
    
    while client.is_closed:     # TODO : Clean this code
        server_stats_alarm = time(hour=23, minute=59)
        
        current_time = datetime.now(sa_timezone).strftime('%H:%M')
        current_time = str(current_time).split(':')
        server_stats_alarm = str(server_stats_alarm).split(':')[:-1]
        current_h, current_m = int(current_time[0]), int(current_time[1])
        server_stats_alarm_h, server_stats_alarm_m = int(server_stats_alarm[0]), int(server_stats_alarm[1])
        h_left = server_stats_alarm_h - current_h; m_left = server_stats_alarm_m - current_m
        
        #server_stats_alarm = current_time

        total_seconds = ((h_left * 60) * 60) + (m_left * 60)

        #print('S:', total_seconds)2

        guild = client.get_guild(int(data.server_id))
        
        if current_time == server_stats_alarm:
            time_stats = TimeStats()
            stats_msg = await get_tday_data(time_stats)
            guild = client.get_guild(int(data.server_id))


            stats = Stats()

            embed_1 = discord.Embed(title=f"{str(time_stats.current_date)}", color=discord.Color.blue())
            embed_1.set_thumbnail(url=guild.icon_url)
            embed_1.add_field(name='Joins/Leaves', value=f"Joins: **{stats_msg[3]}**\nLeaves: **{stats_msg[4]}**")
            embed_1.add_field(name='Messages', value=f"Total messages: **{stats_msg[5]}**")

            embed_2 = discord.Embed(color=discord.Color.blue())
            embed_2.set_image(url='attachment://%s' % stats.filename)

            channel = data.get_useful_channel(cname='ss')
            
            await channel.send(embed=embed_1)
            await channel.send(file=stats.get_stats(), embed=embed_2)          

            total_seconds = ((24 * 60) * 60)

            # Clean up errors
            error_data = read_data_file('errors.json')
            error_data['errors'] = {}
            write_data_file('errors.json', error_data)
        else:
            total_seconds = ((h_left * 60) * 60) + (m_left * 60)
        
        await asyncio.sleep(total_seconds / 2)
    
    
async def rank_msg(member : discord.Member):
    if not member.bot:
        leveling_System = Leveling_System(member)
        msg = leveling_System.rank()
        embed = discord.Embed(
            description=f'{msg[1]}  {msg[2]}\n',
            color=discord.Color.blue()
        )
        embed.add_field(name=msg[3], value=msg[0], inline=False)
        embed.add_field(name='Roles:', value=' '.join(a.mention for a in member.roles[::-1] if not a.name == '@everyone'), inline=False)
        embed.set_author(name=member, icon_url=member.avatar_url)
        return embed


async def member_leave_process(member):
    noob = Leveling_System(member)
    noob.remove_user()
    stats = TimeStats()
    stats.member_leave()
    print(f"{member} has left the server.")


async def reddit_command(*args):
    await reddit(*args)


async def get_iq(member:discord.Member) -> int:
    with open('%siq_scores.json' % data_folder) as f:
        iqscores = json.load(f)
    
    luck = randint(0, 10)
    low, high = 0, 10
    if luck == 9:
        low, high = 10, 420

    if str(member.id) in iqscores:
        if luck == 9:
            if randint(0, 10) != 9: low, high = 0, 10
            iq = randint(low, high)
        else:
            iq = iqscores[str(member.id)]
    else:
        iq = randint(low, high)

    iqscores[str(member.id)] = iq

    with open('%siq_scores.json' % data_folder, 'w') as f:
        json.dump(iqscores, f, indent=4)
    
    return iq


async def get_gay_test():
    says = choice(['**100%** GAY!', 'kinda yea', 'nope! 100% straight', '**69%** gay', "21% gay", '1% gay', '99% gay', '50% gay', '10% gay'])

    rand_say = f'**{randint(0, 100)}**% gay'

    say = choice([rand_say, says])

    return say


async def send_lvl_up_msg(leveled_up):
    leveled_up_msg = f"**{leveled_up[1] if leveled_up[3] != 69 else leveled_up[1].mention}** has level up from {leveled_up[2]} -> **{leveled_up[3]}**"
    channel = Send_Message(data.get_useful_channel(cname='lu'))
    await channel.send(leveled_up_msg)


async def command_success(ctx):
    await ctx.message.add_reaction('✅')


def get_member(member:str) -> discord.Member:
    try:
        return client.get_user(int(member)) # Checks if member is an ID
    except ValueError:
        if member.startswith('<@!'): # Its a member
            return client.get_user(int(member[3:-1]))
        else:
            raise Exception("'%s' member not found." % member)


def read_data_file(filename:str) -> dict:
    with open('%s%s' % (data_folder, filename)) as f:
        content = json.load(f)
    return content


def write_data_file(filename:str, content:dict):
    with open('%s%s' % (data_folder, filename), 'w') as f:
        json.dump(content, f, indent=4)


def create_message_link(guild_id, channel_id, message_id):
    link = 'discord.com/channels/guild_id/channel_id/message_id'.split('/')
    link[2] = str(guild_id)
    link[3] = str(channel_id)
    link[4] = str(message_id)
    link = 'https://%s' % ('/'.join(link))
    return link


async def update_bot(ctx):
    await ctx.send("**Updating...**")
    _code = os.system('echo $(git pull) > update.txt')
    with open('update.txt') as f:
        update_status = f.read()
    
    await ctx.send(embed=discord.Embed(title='Update status:', description='```\n%s```' % update_status).set_footer(text='exit_code: %s' % _code))
    
    with open('update.txt', 'w') as f:
        pass


async def on_dm_message(message):
    if message.author.id == server_owner.id:
        await client.process_commands(message)
        return
    
    if not message.author.bot:
        global dm_messages
        content = await commet_lines(message.content)
        
        if len(message.embeds) != 0 and message.content.startswith('https://'):
            for embed in message.embeds:
                url = embed.to_dict()['url']
                embed = discord.Embed(description='%s\n﹂ %s' % (content, message.id))
                embed.set_author(name=message.author, icon_url=message.author.avatar_url, url=create_message_link('@me', message.channel.id, message.id))
                embed.set_footer(text=message.author.id)
                msg = await server_owner.send(embed=embed)
                await msg.reply(url)

                dm_messages.append(msg.id)
            else:
                return

        embed = discord.Embed(description='%s\n﹂ %s' % (content, message.id), color=discord.Color.blue())
        embed.set_footer(text=message.author.id)
        embed.set_author(name=message.author, icon_url=message.author.avatar_url, url=create_message_link('@me', message.channel.id, message.id))
        msg = await server_owner.send(embed=embed)

        dm_messages.append(msg.id)


async def human_like_send(member:Union[discord.member.Member, discord.channel.TextChannel], message:str):
    if not message.startswith('https://'):
        async with member.typing():
            await asyncio.sleep(len(message) / 10)

    await member.send(message)


async def get_history(ctx, member:discord.Member, limit:int):
    member_dm_history_msg = await member.history(limit=limit).flatten()

    embed = discord.Embed(title='DM history:')
    embed.set_footer(text=str(member.id))
    embed.set_author(name=member, icon_url=member.avatar_url)

    for message in member_dm_history_msg[::-1]:
        content = await commet_lines(message.content)
        embeds = message.embeds

        value = '%s%s' % (content, '' if len(embeds) == 0 else '\n`%s`' % str(embeds))

        embed.add_field(name=message.author, value='%s\n﹂ %i' % (value, message.id), inline=False)
    else:
        await ctx.send(embed=embed)


async def view_message(ctx, member:discord.Member, message_id:int):
    message = await member.fetch_message(message_id)

    embeds = message.embeds
    attachments = message.attachments
    

    if not len(embeds) == 0:
        for embed in embeds:
            if message.content.startswith('https://'):
                url = embed.to_dict()['url']
                await ctx.message.reply(url)
            else:
                await ctx.message.reply(embed=embed)
    elif not len(attachments) == 0:
        await ctx.message.reply("Attachments: %s" % message.attachments)
    else:
        await ctx.message.reply(str(message))


async def commet_lines(message_content):
    return '\n'.join(['> %s' % line for line in message_content.split('\n')])


async def _exit():
    await reddit.reddit.close()
    await client.close()


async def clear_screen(ctx):
    os.system('clear')
    print(ctx.channel, ctx.author)


def make_error_message(error_msg, url='') -> discord.Embed:
    return discord.Embed(
        title=':x: Error:',
        description='> ' + error_msg,
        url=url,
        colour=discord.Color.from_rgb(255, 0, 0)
    )


async def channel_create_embed(channel) -> discord.Embed:
    channel_type = channel.type
    channel_category = channel.category

    des = "%s channel %s create in **%s** category" % (channel_type, channel.mention, channel_category)

    return discord.Embed(description=des, colour=discord.Color.from_rgb(0, 255, 0))


async def channel_delete_embed(channel) -> discord.Embed:
    channel_type = channel.type
    channel_category = channel.category

    des = "%s channel **%s** deleted in **%s** category" % (channel_type, channel, channel_category)

    return discord.Embed(description=des, colour=discord.Color.from_rgb(255, 0, 0))


async def role_create_embed(role) -> discord.Embed:
    des = "name: **%s**: %s" % (role, role.mention)

    return discord.Embed(title="Role created:", description=des, colour=discord.Color.from_rgb(0, 255, 0))


async def role_delete_embed(role) -> discord.Embed:
    des = "name: **%s**" % role

    return discord.Embed(title="Role deleted:", description=des, colour=discord.Color.from_rgb(255, 0, 0))


async def get_changes(before, after) -> dict:
    list_before = inspect.getmembers(before)
    list_after = inspect.getmembers(after)

    changes = {}

    for idx, attr in enumerate(list_after):
        before_attr = list_before[idx]
        if not attr[0].startswith('_') and not str(type(attr[1])) in ["<class 'method'>", "<class 'method-wrapper'>"]:
            if not attr[1] == before_attr[1]:
                changes[attr[0]] = [before_attr[1], attr[1]]

    return changes



# FORM HERE DOWN, THIS IS THE @client.event & @tasks functions

@client.event
async def on_ready():
    global on_ready_time
    global reddit
    reddit = Reddit()
    on_ready_time = datetime.now()
    text = f"**{client.user}** is online @ **{on_ready_time}**" 
    print(text)
    await store_data()
    
    try:
        channel = client.get_channel(int(sys.argv[1:][0]))
        if not channel is None:
            await channel.send(embed=discord.Embed(description=text))
    except Exception:
        pass

    activity = discord.Game(name="%s%s" % (command_prefix, help._callback.__name__), type=3)
    await client.change_presence(activity=activity)
            

@client.event
async def on_message_delete(message):
    check_if_reaction_role_message(str(message.id))

    channel = Send_Message.audit_log()

    embed = discord.Embed(
        description="**%s**'s message deleted in %s\n" % (message.author.mention, message.channel.mention),
        colour=discord.Color.from_rgb(255, 0, 0)
    )
    embed.add_field(name='Message:', value=message.content, inline=False)
    current_time = str(datetime.now(sa_timezone).strftime('%H:%M'))
    if int(current_time.split(':')[0]) > 12:
        current_time = '%i:%i %s' % (int(current_time.split(':')[0]) - 12, int(current_time.split(':')[1]), 'PM')
    else:
        current_time = '%s %s' % (current_time, 'AM')

    embed.set_footer(text=current_time)
    await channel.send(embed=embed)
    
    last_deleted_message[message.channel.id] = {}
    last_deleted_message[message.channel.id]['user'] = message.author.id
    last_deleted_message[message.channel.id]['content'] = message.content
    last_deleted_message[message.channel.id]['time'] = current_time

    
@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        await on_dm_message(message)
    else:
        if any(word in message.content for word in no_no_words):
            await message.delete()
            await warn(message, message.author, reason="Discord Invites")
            return
        if not message.author.bot:
            stats = TimeStats(); stats.on_message()
            user_rank_data = Leveling_System(message.author) # This is doing the leveling system thing
            leveled_up = user_rank_data + int(len(message.content) / 1.5)
            if leveled_up[0]:
                await send_lvl_up_msg(leveled_up)
            
            if message.content.startswith('%sr/' % command_prefix):
                _content = message.content.split('/')
                _content[0] = ''.join([_content[0], '/'])
                message.content = ' '.join(_content)
            
            await client.process_commands(message)

            await user_rank_data.update_live_rank(data)


@client.event
async def on_member_join(member):
    new_member = Leveling_System(member)
    new_member.add_user()
    stats = TimeStats()
    stats.member_join()

    roles_channel = data.get_useful_channel('r')
    rules_channel = data.get_useful_channel(cname='rules')
    if member.bot:
        await member.add_roles(data.get_role('bots'))

    embed = discord.Embed(
        title=f"Welcome {member.name} to {member.guild}",
        description=f"The rules: {rules_channel.mention}\n\nTo get roles, look in {roles_channel.mention}\n\nAny help? ask {client.get_user(int(data.server_owner_id)).mention}" if not member.bot else "This is a bot.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'{member.guild}')
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Info:', value='IQ: **%i**\n%s' % (await get_iq(member), await get_gay_test()), inline=False)
    channel = Send_Message(data.get_useful_channel('w'))
    await channel.send(member.mention, embed=embed)


@client.event
async def on_member_remove(member):
    task = asyncio.create_task(member_leave_process(member))
    embed = discord.Embed(description=f'**{member}** left this server.')
    await Send_Message(data.get_useful_channel('ntl')).send(embed=embed)


@client.event
async def on_raw_reaction_add(payload : discord.RawReactionActionEvent):
    if not payload.user_id == client.user.id:
        if payload.channel_id == data.get_useful_channel(cname='r').id:
            with open('%sreactions.json' % data_folder) as f:
                messages = json.load(f)

            if str(payload.message_id) in messages:
                if str(payload.emoji) in messages[str(payload.message_id)]:
                    role_id = messages[str(payload.message_id)][str(payload.emoji)]
                    role = discord.utils.get(client.get_guild(payload.guild_id).roles, id=int(role_id))
                    user = discord.utils.get(client.get_guild(payload.guild_id).members, id=payload.user_id)
                    await user.add_roles(role)
            else:
                pass
        elif payload.channel_id == data.get_useful_channel(cname='rules').id:
            if str(payload.message_id) == '823307869746495568': # This ID is the rules message's ID
                user = discord.utils.get(client.get_guild(payload.guild_id).members, id=payload.user_id)
                role = discord.utils.get(client.get_guild(payload.guild_id).roles, id=int(data.get_role(cname='humans').id))
                await user.add_roles(role)
        else:
            if payload.emoji.name == '❌':
                errors_data = read_data_file('errors.json')

                if str(payload.message_id) in errors_data['errors']:
                    error_msg = errors_data['errors'][str(payload.message_id)]['error']
                    error_type = errors_data['errors'][str(payload.message_id)]['type']

                    embed = make_error_message(error_msg)
                    embed.set_footer(text=error_type)

                    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)

                    await message.reply(embed=embed)

                    del errors_data['errors'][str(payload.message_id)]

                    write_data_file('errors.json', errors_data)
            elif payload.emoji.name == '✅':
                if not announce_message is None:
                    for msg in announce_message:
                        if payload.message_id == msg.id:
                            await msg.delete()
                            await announce_message[msg].delete()
                            return
                if not mod_files is None:
                    if payload.message_id in mod_files:
                        for filename in mod_files[payload.message_id]:
                            with open('%s%s' % (data_folder, filename), 'w') as f:
                                for line in mod_files[payload.message_id][filename]:
                                    f.write('%s\n' % line)
                            channel = client.get_channel(payload.channel_id)
                            await channel.send('Done writing.')
            else:
                global ttt_running
                if len(ttt_running) > 0:
                    try:
                        for ttt_game in ttt_running:
                            if payload.emoji.name in ttt_game.reactions:
                                if payload.message_id == ttt_game.game_msg.id:
                                    if payload.user_id == ttt_game.turn.id:
                                        await ttt_game.move(payload.emoji)
                            elif payload.emoji.name == '🔄':
                                if (payload.user_id in [ttt_game.player_1.id, ttt_game.player_2.id]) or (ttt_game.player_1.bot and ttt_game.player_2.bot):
                                    if not ttt_game.whos_turn_msg is None:
                                        if payload.message_id == ttt_game.whos_turn_msg.id:
                                            ttt_running.remove(ttt_game)
                                            await tictactoe(ctx=ttt_game.ctx, player1=ttt_game.player_1, player2=ttt_game.player_2)
                                            ttt_game.destroy = False
                    except NameError:
                        pass
    
    
@client.event
async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
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


@client.event
async def on_command_error(ctx, error):
    error_filename = 'errors.json'

    errors = read_data_file(error_filename)

    if not 'errors' in errors:
        errors['errors'] = {}    
    
    errors['errors'][str(ctx.message.id)] = {}
    errors['errors'][str(ctx.message.id)]['error'] = str(error)
    errors['errors'][str(ctx.message.id)]['type'] = str(type(error))

    if not 'do_not_raise' in errors:
        errors['do_not_raise'] = []

    write_data_file(error_filename, errors)

    await ctx.message.add_reaction('❌')

    if not str(type(error)) in errors['do_not_raise']:
        error_channel = data.get_useful_channel('ore')

        embed = make_error_message(str(error), url=create_message_link(ctx.guild.id, ctx.channel.id, ctx.message.id))
        embed.set_footer(text=str(type(error)))

        await error_channel.send(embed=embed)
        
        raise error
    

@client.event
async def on_message_edit(before, after):
    channel = Send_Message.audit_log()

    embed = discord.Embed(description="%s edited a message in %s" % (after.author.mention, after.channel.mention), colour=discord.Color.blue())
    embed.set_author(name='message_link', url=create_message_link(after.guild.id, after.channel.id, after.id), icon_url=after.author.avatar_url)
    embed.add_field(name="Before:", value=await commet_lines(before.content), inline=False)
    embed.add_field(name="After:", value=await commet_lines(after.content), inline=False)

    await channel.send(embed=embed)


@client.event 
async def on_private_channel_delete(channel):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await channel_delete_embed(channel))


@client.event
async def on_private_channel_create(channel):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await channel_create_embed(channel))


@client.event
async def on_guild_channel_delete(channel):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await channel_delete_embed(channel))


@client.event 
async def on_guild_channel_create(channel):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await channel_create_embed(channel))


@client.event
async def on_guild_channel_update(before, after):
    a_channel = Send_Message.audit_log()

    list_before = inspect.getmembers(before)
    list_after = inspect.getmembers(after)

    changes = await get_changes(before, after)

    embed = discord.Embed(title="Channel update:", description=after.mention, colour=discord.Color.blue())

    if "members" in changes and "changed_roles" in changes:
        del changes["members"]
    
    if 'overwrites' in changes:
        del changes['overwrites']

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

    await a_channel.send(embed=embed)
        

@client.event
async def on_member_update(before, after):
    a_channel = Send_Message.audit_log()

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


@client.event
async def on_user_update(before, after):
    a_channel = Send_Message.audit_log()

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


@client.event
async def on_guild_update(before, after):
    a_channel = Send_Message.audit_log()

    changes = await get_changes(before, after)

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

    await a_channel.send(embed=embed)


@client.event
async def on_guild_role_create(role):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await role_create_embed(role))


@client.event
async def on_guild_role_delete(role):
    a_channel = Send_Message.audit_log()

    await a_channel.send(embed=await role_delete_embed(role))


@client.event
async def on_guild_role_update(before, after):
    a_channel = Send_Message.audit_log()

    changes = await get_changes(before, after) 

    embed = discord.Embed(title="Role update:", description=after.mention, colour=discord.Color.blue())

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

    await a_channel.send(embed=embed)


@client.event
async def on_member_ban(guild, user):
    sa_channel = data.get_useful_channel(cname='sa')

    await sa_channel.send(embed=discord.Embed(title='Member banned!', description="%s is banned from **%s**" % (user.mention, guild), colour=discord.Color.from_rgb(255, 0, 0)).set_author(name=user, icon_url=user.avatar_url))


@client.event
async def on_member_unban(guild, user):
    sa_channel = data.get_useful_channel(cname='sa')

    await sa_channel.send(embed=discord.Embed(title='Member unban!', description="%s is unban from **%s**" % (user.mention, guild), colour=discord.Color.from_rgb(0, 255, 0)).set_author(name=user, icon_url=user.avatar_url))


@client.event
async def on_invite_create(invite):
    a_channel = Send_Message.audit_log()

    des = "**Created by:** %s\n\nmax_age: **%s**s\nmax_uses: **%s**\n\nChannel: %s\n\nUrl: %s" % (invite.inviter.mention, invite.max_age, invite.max_uses, invite.channel.mention, invite)

    await a_channel.send(embed=discord.Embed(title="Invite created", description=des, colour=discord.Color.from_rgb(0, 255, 0)))


@client.event
async def on_invite_delete(invite):
    a_channel = Send_Message.audit_log()

    des = "**Channel:** %s\n\nUrl: %s" % (invite.channel.mention, invite)

    await a_channel.send(embed=discord.Embed(title="Invite deleted", description=des, colour=discord.Color.from_rgb(255, 0, 0)))


#UP HERE ALL THE @client.event ^^ 


#########################################################

#########################################################


#DOWN HERE IS ALL THE COMMANDS \/ @client.command()


@client.command(category='Owner', description="Command testing")
@commands.is_owner()
async def test(ctx): # Here i test commands
    try:
        rmsg = await Reference(ctx.message).get_reference()
    except Reference.NoneReference as e:
        await ctx.send(e)
    else:
        await rmsg.reply(rmsg.content)
    
    
@client.command(category='Owner', description='To enable a text channel')
@commands.is_owner()
async def enable(ctx, channel : discord.TextChannel=None):
    if channel is None: 
        channel = ctx.channel
    channel = Send_Message(channel)
    await ctx.send(channel.enable())
    
    
@client.command(category='Owner', description='Disable a text channel')
@commands.is_owner()
async def disable(ctx, channel : discord.TextChannel=None):
    if channel is None: 
        channel = ctx.channel
    channel = Send_Message(channel)
    await ctx.send(channel.disable())


@client.command(pass_context=True, description="Joins the voice channel", category='Voice')
async def join(ctx):
    if ctx.author.voice:
        voice_channel = ctx.author.voice
        await voice_channel.channel.connect()
    else:
        await ctx.send("You not in a voice channel.")


@client.command(pass_context=True, aliases=['leave'], description='Leave the voice channel', category='Voice')
async def disconnect(ctx):
    if ctx.author.voice:
        try:
            await ctx.guild.voice_client.disconnect()
        except AttributeError: 
            await ctx.send("I'm not in that voice channel.")
        else:
            await ctx.send("Disconnected.")
    else:
        await ctx.send("You not in that voice channel. Bruh")


@client.command(category='Owner', description='Embed testing')
@commands.is_owner()
async def embed(ctx, channel:discord.TextChannel, *, title_msg): # Here i test my embed messages 
    title, msg = title_msg.split('\\')
    await channel.send(embed=discord.Embed(title=title, description=msg, colour=discord.Color.blue()))



@client.command(category='Owner', description="To DM someone as bot\nOr see the messages history, or delete messages")
@commands.is_owner()
async def dm(ctx, argument : Union[discord.Member, discord.TextChannel, str], *, args : Union[discord.Member, str]=None):
    def to_(member:discord.Member) -> discord.Embed:
        return discord.Embed().set_author(name=member, icon_url=member.avatar_url)

    
    if isinstance(argument, (discord.member.Member, discord.channel.TextChannel)):
        if args is None: return await ctx.send("You can't send empty message.")

        await human_like_send(argument, args)
        if type(argument) is discord.member.Member:
            await ctx.message.reply(embed=to_(member=argument))
    elif isinstance(argument, str):
        if argument in ['hist', 'history']:
            if isinstance(args, discord.member.Member):
                limit = 10
                member = args
            else:
                _args = args.split(' ')
                member = discord.utils.get((server).members, id=int(_args[0]))
                limit = int(_args[1])

            await get_history(ctx, member, limit)
        elif argument in ['del', 'delete']:
            try:
                rmsg = await Reference(ctx.message).get_reference()
            except Reference.NoneReference:
                _args = args.split(' ')
                member_id = int(_args[0])
                messages_id = _args[1:]

                member = client.get_user(member_id)
            else:
                embed_dict = rmsg.embeds[0].to_dict()
                member_id = int(embed_dict['footer']['text'])
                messages_id = args.split(' ')
                
                member = client.get_user(member_id)
            finally:
                for msg_id in messages_id:
                    msg = await member.fetch_message(int(msg_id))

                    await msg.delete()
                else:
                    await command_success(ctx)
        elif argument in ['view', '-d']:
            try:
                rmsg = await Reference(ctx.message).get_reference()
            except Reference.NoneReference as e:
                await ctx.send(e)
            else:
                embed = rmsg.embeds[0].to_dict()
                member_id = int(embed['footer']['text'])
                member = client.get_user(member_id)
                message_id = int(args or embed['description'].split(' ')[-1]) 
                await view_message(ctx, member, message_id)
        else:
            try:
                rmsg = await Reference(ctx.message).get_reference()
            except Reference.NoneReference as e:
                return await ctx.send(e)
            else:
                if rmsg.id in dm_messages:
                    embed = rmsg.embeds[0]
                    embed_dict = embed.to_dict()

                    member_id = int(embed_dict['footer']['text'])
                    message_id = int(embed_dict['description'].split(' ')[-1])

                    member = client.get_user(member_id)

                    message_to_send = ' '.join([argument, args or ''])

                    async with member.typing():
                        await asyncio.sleep(len(message_to_send) / 10)

                    user_msg = await member.fetch_message(message_id)

                    await user_msg.reply(message_to_send)

                    await command_success(ctx)
                    #await ctx.message.reply(embed=to_(member))
    else:
        print('huh?')
        print(type(argument))


@client.command()
async def set_status(ctx, status_num):
    pass # TODO make it so a user can set the bot status


@client.command(aliases=['cls_dm'], category='Owner', description='Deletes the bot messages')
@commands.is_owner()
async def cls_ur_msg(ctx, amount=50): # This will delete this bot message's
    if ctx.author.id == server_owner.id:
        messages = await ctx.history(limit=amount).flatten()
        for msg in messages:
            if msg.author == client.user:
                await msg.delete()


@client.command(category='Info', description="See what's your rank")
async def rank(ctx, member : discord.Member=None):
    member = member or ctx.author
    user_rank = Leveling_System(member)
    await ctx.send(embed=await user_rank.rank_msg(member))


@client.command(category='Mod', description="Deletes messages in text channel")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount + 1)


@client.command(category='Mod', description="To kick a dumb fuck")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.message.add_reaction('🦶🏽')
    await ctx.send(f'**{member}** kicked!')


@client.command(category='Mod', description='To ban a poes')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    bans_says = ['**{}** is banned from this server.', 'Yes! That poes **{}** is banned from this server!']
    await member.ban(reason=reason)
    await ctx.message.add_reaction('✅')
    await ctx.send(choice(bans_says).format(member))


@client.command(description="List all the members that got banned.", category='Mod')
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


@client.command(category='Mod', description="To unban a former member")
@commands.has_permissions(ban_members=True)
async def unban(ctx, id : int):
    try:
        user = await client.fetch_user(id)
        await ctx.guild.unban(user)
    except discord.errors.NotFound as e:
        await ctx.message.add_reaction('❌')
        print(e)
    else:
        await ctx.message.add_reaction('✅')


@client.command(description="The bot's latency", category='Info')
async def ping(ctx):
    await ctx.message.reply(embed=discord.Embed(description=f'**{round(client.latency * 1000)}**ms', colour=discord.Color.blue()))


@client.command(category='Info', description="The total messages")
async def msg_count(ctx):
    stats = TimeStats()
    await ctx.send(f"Total message's: {stats.cal_total_messages()}")


@client.command(category='Info', description="Get info of a member")
async def mi(ctx, member : discord.Member=None):
    member = member or ctx.author

    created = member.created_at.strftime(f"%A, %B %d %Y @ %H:%M %p")
    joined = member.joined_at.strftime(f"%A, %B %d %Y @ %H:%M %p")
    roles = ' '.join(a.mention for a in member.roles[::-1] if not a.name == '@everyone')

    line1 = f"Account created at: **{created}**"
    line2 = f"Joined this server at: **{joined}**"
    line3 = f"Roles: {roles}"

    embed = discord.Embed(
        title=f"{member} info:",
        description=f"{line1}\n\n{line2}\n\n{line3}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar_url)

    await ctx.send(embed=embed)
    
    
@client.command(category='Info', description="See the user's profile pic")
async def pfp(ctx, member : discord.Member=None):
    member = member or ctx.author
    await ctx.send(member.avatar_url)
    

@client.command(aliases=['ttt'], category='Fun', description="Tic-tac-toe game")
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
    
    global ttt_running
    ttt_game = TicTacToe(player1, player2, data, ctx, ttt_running, client)
    ttt_running.append(ttt_game)
    ttt_game.all_running_ttt = ttt_running
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
    
    
@client.command(category='Admin', description="To warn a dumb fuck")
@commands.has_permissions(administrator=True)
async def warn(ctx, user : discord.Member, *, reason=None):
    if user.id == ctx.guild.owner.id:
        await ctx.send("Fuck you! %s" % ctx.author.mention)
        return 
    with open('%swarnings.json' % (data_folder)) as f:
        warnings = json.load(f)

    reason_text = f"Reason: **{reason}**" if not reason == None else f"Reason: {reason}"

    if str(user.id) in warnings:
        warnings_count = len([warn for warn in warnings[str(user.id)]]) + 1
        reason_text = '%s\n%s' % (reason_text, 'This is your %ith warning.' % (warnings_count))

    embed = discord.Embed(
        title=f"**⚠️ !!! YOU HAVE BEEN WARN !!!** ⚠️",
        description=reason_text,
        color=discord.Color.red()
    )
    embed.set_footer(text=f'{ctx.guild} • owner: {ctx.guild.owner}')
    
    try:
        warning_message = await user.send(embed=embed)
    except discord.errors.HTTPException as e:
        raise Exception('**%s**' % (e))
    else:
        try:
            await ctx.send('Warning sent.')
        except:
            pass

        if not str(user.id) in warnings: warnings[str(user.id)] = {}
        warnings[str(user.id)][str(warning_message.id)] = reason

        with open('%swarnings.json' % (data_folder), 'w') as f:
            json.dump(warnings, f, indent=4)   


@client.command(aliases=['warns', 'warns_id'], category='Admin', description="List all the members warnings")
@commands.has_permissions(administrator=True)
async def warnings(ctx, member : discord.Member=None):
    with open('%swarnings.json' % (data_folder)) as f:
        warnings = json.load(f)
    
    embed = discord.Embed(
        title="Warning List",
        color=discord.Color.red()
    )
    if member is None:
        for user_id in warnings:
            user = client.get_user(int(user_id))
            if ctx.message.content.startswith('%swarns_id' % (command_prefix)): user = '%s (%i)' % (user.name, user.id)
            user_reasons = []
            for msg_id in warnings[user_id]:
                if ctx.message.content.startswith('%swarns_id' % (command_prefix)):
                    user_reasons.append('• `%s` ~ (%s)' % (str(warnings[user_id][msg_id]), msg_id))    
                else:
                    user_reasons.append('• `%s`' % (str(warnings[user_id][msg_id])))
            user_reasons = '\n'.join(user_reasons)
            embed.add_field(name='%s, reason(s):' % user, value=user_reasons, inline=False)
    else:
        user_reasons = []
        for msg_id in warnings[str(member.id)]:
            if ctx.message.content.startswith('%swarns_id' % (command_prefix)):
                user_reasons.append('• `%s` ~ (%s)' % (str(warnings[str(member.id)][msg_id]), msg_id))    
            else:
                user_reasons.append('• `%s`' % (str(warnings[str(member.id)][msg_id])))
        user_reasons = '\n'.join(user_reasons)
        if ctx.message.content.startswith('%swarns_id' % (command_prefix)): member = '%s (%i)' % (member.name, member.id)
        embed.add_field(name='%s, reason(s):' % member, value=user_reasons, inline=False)

    await ctx.send(embed=embed)


@client.command(category='Owner', description="Deletes a memebr's warning")
@commands.is_owner()
async def del_warn(ctx, id):
    with open(f'{data_folder}warnings.json') as f:
        warnings = json.load(f)

    if id.startswith('<@!'):
        id = id[3:-1]

    async def delete_warn(member_id, message_id):
        member = client.get_user(int(member_id))
        messages = await member.history(limit=100).flatten()
        for msg in messages:
            if int(message_id) == msg.id:
                await msg.delete()
                return 0
        return 1

    async def delete_warns(member_id, messages_id : list):
        member = client.get_user(int(member_id))
        messages = await member.history(limit=100).flatten()
        for msg in messages:
            if str(msg.id) in messages_id:
                await msg.delete()
        else:
            del warnings[member_id]
            return 0

    exit_code = 1
    if str(id) in warnings:
        exit_code = await delete_warns(id, [msg_id for msg_id in warnings[id]])
    else:
        try:
            for user_id in warnings:
                if str(id) in warnings[user_id]:
                    if await delete_warn(user_id, id) == 0:
                        del warnings[user_id][str(id)]
                        exit_code = 0
                if warnings[user_id] == {}:
                    del warnings[user_id]
                    exit_code = 0
        except RuntimeError:
            pass

    if exit_code == 1:
        await ctx.send('**%s** not found.' % (id))
    else:
        with open(f'{data_folder}warnings.json', 'w') as f:
            json.dump(warnings, f, indent=2)

        await ctx.message.add_reaction('✅')


#@client.command(aliases=['server_update', '__sa__'])
#@commands.has_permissions(administrator=True)
#async def server_announcement(ctx, *, args=None):
#    server_announcement_channel = data.get_useful_channel(cname='sa')
#    await server_announcement_channel.send(msg)
#    await ctx.message.add_reaction('✅')


@client.command(category='Admin', description='Reply to a message to be announced')
@commands.has_permissions(administrator=True)
async def announce(ctx, *, args=None):
    reference = ctx.message.reference
    if not reference is None:
        channel = client.get_channel(reference.channel_id)
        replied_message = await channel.fetch_message(reference.message_id)

        embed = discord.Embed(description=replied_message.content)
        embed.set_author(name=replied_message.author, icon_url=replied_message.author.avatar_url)

        server_announcement_channel = data.get_useful_channel(cname='sa')   

        await server_announcement_channel.send('@everyone' if args == 'everyone' else args, embed=embed)

        await ctx.message.add_reaction('✅')

        global announce_message
        announce_message = announce_message or {}
        announce_message[ctx.message] = replied_message
        await asyncio.sleep(10)
        try:
            del announce_message[ctx.message]
        except KeyError:
            pass
    else:
        await ctx.send("Reply to a message to be announced.")


@client.command(category='Owner', description='Restart the bot')
@commands.is_owner()
async def reboot(ctx, *args):
    arguments = {'update': update_bot, 'clear': clear_screen}

    for arg in args:
        try:
            await arguments[arg](ctx)
        except KeyError as e:
            raise Exception("Argument %s not found." % e)
    
    await ctx.send("Rebooting...")
    
    with open('reboot_id', 'w') as f:
        f.write(str(ctx.channel.id))

    await _exit()


@client.command(category='Owner', description='Most photos to Instagram')
@commands.is_owner()
async def instagram(ctx, image_url, *, caption=" "):
    _insta = insta.Instagram_Bot(sys, requests, shutil, os)
    await _insta.main(image_url, caption)
    await ctx.message.add_reaction('✅')


@client.command(category='Admin', description="It's not needed anymore")
@commands.has_permissions(administrator=True)
async def add_role(ctx, role : discord.Role, price, cname):
    with open(f'{data_folder}shop.json') as f:
        shop = json.load(f)
    shop['roles'][str(role.id)] = {}
    shop['roles'][str(role.id)]['name'] = role.name
    shop['roles'][str(role.id)]['price'] = int(price)
    shop['roles'][str(role.id)]['cname'] = cname
    with open(f'{data_folder}shop.json', 'w') as f:
        json.dump(shop, f, indent=2)


@client.command(description="See how many lines of code the bot have", category='Info')
async def lines(ctx):
    lines = 0

    for file in os.scandir():
        if file.name.endswith('.py') or file.name.endswith('.sh'):
            with open(file.name) as f:
                for _ in f.readlines():
                    lines += 1

    await ctx.send('I have **%i** lines of code.' % (lines))


@client.command(category='Info', description='Get the user ID')
async def id(ctx, member : discord.Member=None):
    member = member or ctx.author

    await ctx.message.reply('**%i**' % (member.id))


@client.command(category='Admin', description="Reads the json file")
@commands.has_permissions(administrator=True)
async def view_json(ctx, file_name):
    if file_name.endswith('.json'):
        with open('%s%s' % (data_folder, file_name)) as f:
            try:
                await ctx.send("```json\n%s\n```" % (f.read()))
            except Exception:
                await ctx.send(file=discord.File('%s%s' % (data_folder, file_name)))
    else:
        raise Exception("**%s does not end with '.json'**" % (file_name))


@client.command(category='Admin', description="List all the json files")
@commands.has_permissions(administrator=True)
async def list_json(ctx):
    json_files = []
    for f in os.scandir(data_folder):
        if f.name.endswith('.json'):
            json_files.append(f.name)
    else:
        await ctx.send('\n'.join(json_files))


@client.command(category='Info', description="Just pass the user id in and you will see who is it")
async def who(ctx, user_id : int):
    await ctx.message.reply('**%s**' % (client.get_user(user_id)))


@client.command(category='Info', description="See the members status")
async def status(ctx, member : discord.Member=None, args=None):
    member = member or ctx.author
    try:
        t = str(member.activities[0].type).replace('ActivityType.', '')
        t = '%s%s' % (t[0].upper(), t[1:])
        des = '%s **%s**' % (t, str(member.activities[0].name))
        if args == '-d':
            try:
                des = '%s\n**%s**\n%s' % (des, member.activities[1].name, member.activities[2].details)
            except IndexError:
                try:
                    des = '%s\nGame: **%s**' % (des, member.activities[1].name)
                except IndexError:
                    pass
    except IndexError:
        await ctx.send("Nothing.")
    else:
        embed = discord.Embed(
            title="%s's status:" % member.name,
            description=des
        )
        await ctx.send(embed=embed)


@client.command(category='Fun', description="IQ test, see how smort you are")
async def iqtest(ctx):
    member = ctx.author
    
    iq = await get_iq(member)

    await ctx.send("%s's IQ is: **%i**" % (member.name, iq))


@client.command(category='Info', description="List all the members IQ")
async def iqlist(ctx):
    with open('%siq_scores.json' % data_folder) as f:
        iqscores = json.load(f)

    users = []
    
    for user_id in iqscores:
        try:
            users.append('%s IQ score: **%i**' % (client.get_user(int(user_id)).mention, iqscores[user_id]))
        except AttributeError:
            users.append(str(client.get_user(int(user_id))))

    embed = discord.Embed(
        title='%s members IQ:' % ctx.guild,
        description='\n'.join(users)
    )
    await ctx.send(embed=embed)


@client.command(category='Admin', description="List all the Python files")
@commands.has_permissions(administrator=True)
async def list_scripts(ctx):
    py_files = [py_file.name for py_file in os.scandir() if py_file.name.endswith('.py') or py_file.name.endswith('.sh')]
    
    for idx, file in enumerate(py_files):
        lines = 0
        with open(file) as f:
            for line in f.readlines():
                lines += 1
        py_files[idx] = '`%s` : **%i** lines' % (file, lines)

    embed = discord.Embed(
        title="All the script files:",
        description='\n'.join(py_files)
    )
    await ctx.send(embed=embed)


@client.command(category='Info', description="See the last deleted message in a text channel")
async def snipe(ctx):
    if ctx.channel.id in last_deleted_message:
        embed = discord.Embed(
            description="Last deleted message in %s from %s @ **%s**:" % (ctx.channel.mention, 
            client.get_user(last_deleted_message[ctx.channel.id]['user']).mention,
            last_deleted_message[ctx.channel.id]['time']
            )
        )
        embed.add_field(name='Message:', value=last_deleted_message[ctx.channel.id]['content'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("There's no recently deleted message in %s" % (ctx.channel.mention))


@client.command(category='Info', description="List all current running tic-tac-toe games")
async def list_ttt(ctx):
    des = str()
    for ttt in ttt_running:
        des = '%s\n%s' % (des, ttt)
    embed = discord.Embed(
        title='All running tic-tac-toe games:', 
        description=des
    )
    await ctx.send(embed=embed)

@client.command(category='Owner', description='You know... spam someone :>')
@commands.is_owner()
async def spam(ctx, member : discord.Member, *args):
    if not member.bot:
        if args[0] == 'file':
            file_content = None
            with open(args[1]) as f:
                file_content = f.readlines()
            await ctx.send("Going to spam **%s**\nFile: **%s**, **%i** lines." % (member.name, args[1], len(file_content)))
            for line in file_content:
                try:
                    await member.send(line)
                except discord.errors.HTTPException:
                    pass
        else:
            for _ in range(int(args[1])):
                await member.send(args[0])
        await ctx.send('Done spamming **%s**' % member)
    else:
        await ctx.send("Cannot spam **%s**, because **it's a bot.**" % (member))


@client.command(category='Owner', description="Reaction roles: %snewrr <message_id> emoji @role / emoji @role / etc..." % command_prefix)
@commands.is_owner()
async def newrr(ctx, message_id:int, *, args:str):
    roles_channel = data.get_useful_channel(cname='r')

    message = await roles_channel.fetch_message(message_id)
    
    with open('%sreactions.json' % data_folder) as f:
        blocks = json.load(f)
        blocks[str(message.id)] = {}
    
    for block in args.split(' / '):
        emoji_and_role = block.split(' ')
        blocks[str(message.id)][emoji_and_role[0]] = int(emoji_and_role[1][3:-1])
        await message.add_reaction(emoji_and_role[0])
    else:
        with open('%sreactions.json' % data_folder, 'w') as f:
            json.dump(blocks, f, indent=4)

    await ctx.message.delete()


@client.command(category='Info', description="See how long is the bot online for")
async def uptime(ctx):
    current_time = datetime.now()
    cal_uptime = current_time - on_ready_time
    
    async def over_a_day(cal):
        cal = str(cal).split(', ')
        if len(cal) == 1: 
            raise AttributeError
        cal[1] = cal[1].split('.')[0].split(':')
        cal[1][0] = '**%s**hrs' % str(cal[1][0])
        cal[1][1] = '**%s**m' % str(cal[1][1])
        cal[1][2] = '& **%s**s' % str(cal[1][2])
        cal[1] = ', '.join(cal[1])
        cal = ', '.join(cal)
        return cal

    async def less_than_a_day(cal):
        cal = str(cal).split('.')[0].split(':')
        if cal[0] == '0' and cal[1] == '00':
            return '**%s** seconds' % (cal[2])
        elif cal[0] == '0':
            return '**%s**m & **%s**s' % (cal[1], cal[2])
        else:
            cal[0] = '**%s**hrs' % (cal[0])
            cal[1] = '**%s**m' % (cal[1])
            cal[2] = '& **%s**s' % (cal[2])
            cal = ', '.join(cal)
            return cal
    
    try:
        cal_uptime = await over_a_day(str(cal_uptime))
    except AttributeError:
        cal_uptime = await less_than_a_day(str(cal_uptime))
    finally:
        embed = discord.Embed()
        embed.set_author(name=client.user, icon_url=client.user.avatar_url)
        embed.add_field(name='Uptime:', value=cal_uptime)
        await ctx.send(embed=embed)


@client.command(category='Owner', description='List all members or roles')
@commands.is_owner()
async def listall(ctx, members_or_role:str):
    if members_or_role.lower() == 'roles':
        the_list = [role for role in ctx.guild.roles if not str(role) == '@everyone']
    elif members_or_role.lower() == 'members':
        the_list = ctx.guild.members 
    else:
        return await ctx.send("List all WHAT?")

    await ctx.send(embed=discord.Embed(title='%i total:' % len(the_list), description='\n'.join([thing.mention for thing in the_list])))


@client.command(category='Fun', description='See how GAY someone is.')
async def gaytest(ctx, member:discord.Member=None):
    member = member or ctx.author

    say = await get_gay_test()

    await ctx.send("%s is... %s" % (member.name, say))


@client.command(aliases=['g'], category='Fun', description='You must enter a number between 0-6 & if you and bot have the same number you get exp')
async def guess(ctx, user_guess:int):
    if user_guess >= 0 and user_guess <= 6:
        bot_guess = randint(0, 6)
        
        embed = discord.Embed(description="I guess: **%i**\nYou guessed: **%i**"  % (bot_guess, user_guess))
        await ctx.send(embed=embed)
        if user_guess == bot_guess:
            exp = choice([600, 1000, 500, 400, 1200, 4000, 10, 1, 69, 666, 777, 999])
            user = Leveling_System(ctx.author)
            leveled_up = user + exp
            if leveled_up[0]: # Check if user leveled up
                await send_lvl_up_msg(leveled_up)
            await ctx.send("Wow! + **%i** exp" % exp)
    else:
        await ctx.send("You must guess between 0-6")


@client.command(description="Reply to a message a forward it to a member", category='Info')
async def forward(ctx, *members):
    if members == ():
        members = [str(ctx.author.id)]

    try:
        rmsg = await Reference(ctx.message).get_reference()
    except Reference.NoneReference as e:
        return await ctx.message.reply(e)
    else:
        link = create_message_link(rmsg.guild.id, rmsg.channel.id, rmsg.id)
        
        embed = discord.Embed(description=rmsg.content)
        embed.set_footer(text='Forwarded')
        embed.set_author(name='Message link', url=link, icon_url=rmsg.author.avatar_url)

        for member in members:
            await get_member(member).send('From **%s**' % ctx.author, embed=embed)
        else:
            await command_success(ctx)
    

@client.command(category='Owner', description='Modify the json files')
@commands.is_owner()
async def mod_json_file(ctx, file_name:str):
    if file_name.endswith('.json'):
        with open('%s%s' % (data_folder, file_name)) as f:
            current_file_content = f.read()

        reference = ctx.message.reference
        if not reference is None:
            channel = client.get_channel(reference.channel_id)
            replied_message = await channel.fetch_message(reference.message_id)
        else:
            return await ctx.send("Reply to a message (That's formatted to json)")

        new_file_content = []

        if replied_message.content.startswith('```json') and replied_message.content.endswith('```'):
            for i in replied_message.content.split('\n')[1:-1]:
                new_file_content.append(i)
        else:
            return await ctx.send("Format it in json.")

        msg = await ctx.send("```json\n%s\n```:arrow_down::arrow_down:To:arrow_down::arrow_down:\n%s" % (current_file_content if len(current_file_content) < 4000 else '%s\n\n**Content too long**' % current_file_content[3900:], replied_message.content))
        await msg.add_reaction('✅')
        global mod_files
        mod_files = mod_files or {}
        mod_files[msg.id] = {}
        mod_files[msg.id][file_name] = new_file_content
    else:
        raise Exception("**%s does not end with '.json'**" % (file_name))


@client.command(category='Owner', description="Change the bot's prefix")
@commands.is_owner()
async def set_prefix(ctx, new_prefix:str):
    config = read_data_file(filename='config.json')

    config['prefix'] = new_prefix

    write_data_file(filename='config.json', content=config)

    await command_success(ctx)


@client.command(category='Info', description="To see all the commands:\n`%shelp all`" % command_prefix)
async def help(ctx, command_name:str=None):
    categories = {}
    command_category = ''
    embed = discord.Embed()

    for command in client.all_commands:
        category = str(vars(client.all_commands[command])['__original_kwargs__'].get('category'))
        description = str(vars(client.all_commands[command])['__original_kwargs__'].get('description'))
        if not category in categories:
            categories[category] = {}

        categories[category][command] = {}
        categories[category][command]['description'] = description

    if command_name == 'all':
        embed.title = "All Commands:"
        embed.set_footer(text='%shelp <command_name> or <category_name>' % command_prefix)
        for category in categories:
            embed.add_field(name=category, value="```\n%s```" % '\n'.join(categories[category]))
    else:
        if command_name is None:
            embed.title = 'Category:'
            embed.set_footer(text='%shelp <category_name>' % command_prefix)
            for cate in categories:
                embed.add_field(name=cate, value=str(len(categories[cate])))
        else:
            try:
                _list = categories[command_name]
                embed.title = 'Commands:'
                embed.description = '```\n%s```**%s** category' % ('\n'.join(_list), command_name)
                embed.set_footer(text='%shelp <command_name>' % command_prefix)
            except KeyError:
                found = False
                for category in categories:
                    if command_name in categories[category]:
                        found = True
                        command_category = category
                        _list = command_name
                        description = categories[category][command_name]['description']
                        command_args = ' '.join(['<%s>' % arg for arg in list(vars(client.all_commands[_list])['params'])[1:]])
                        _list = '%s%s %s' % (command_prefix, command_name, command_args)
                        embed.description = '```\n%s```Description:\n**%s**\n\n**%s** category' % (_list, description, command_category)
                        break
                else:
                    if not found:
                        return await ctx.send("Huh? help with what command!?")

    await ctx.send(embed=embed)


@client.command(category='Owner')
@commands.is_owner()
async def add_exp(ctx, member:discord.Member, exp_amount:int):
    member_exp = Leveling_System(member)
    leveled_up = member_exp + exp_amount
    if leveled_up[0]:
        await send_lvl_up_msg(leveled_up)


@client.command(category='Admin')
@commands.has_permissions(administrator=True)
async def pin(ctx):
    try:
        rmsg = await Reference(ctx.message).get_reference()
    except Reference.NoneReference as e:
        return await ctx.send(e)
    else:
        await rmsg.pin()


@client.command(description='To view the source code of a command.', category='Info')
async def source_code(ctx, command_name:str):
    try:
        command = client.all_commands[command_name]._callback
        _source_code = inspect.getsource(command)

        source_file = 'source_code.py'
        with open(source_file, 'w') as f:
            f.write(_source_code)
        
        file = discord.File(source_file)
        
        await ctx.send(embed=discord.Embed(description='**%s** source code:' % command_name, colour=discord.Colour.green()), file=file)

        with open(source_file, 'w') as f:
            f.write('')
    except KeyError as e:
        raise Exception("Command %s not found." % e)


@client.command(category='Owner', description="Reply to a error message and ot won't be raised.")
@commands.is_owner()
async def dnr(ctx):
    try:
        # My own class that returns the replied message.
        rmsg = await Reference(ctx.message).get_reference()
    except Reference.NoneReference as e: 
        # If the user didn't reply to a message
        return await ctx.message.reply(e)
    else:
        # If the user has replied to a message
        embed_footer = str(rmsg.embeds[0].to_dict()['footer']['text'])
        
        if embed_footer.startswith('<class') and embed_footer.endswith('>'):
            error_data = read_data_file('errors.json')

            if embed_footer in error_data['do_not_raise']:
                return await ctx.send("It's already 'dnr'")

            error_data['do_not_raise'].append(embed_footer)

            write_data_file('errors.json', error_data)

            await command_success(ctx)
        else:
            await ctx.send("'%s' does not look like an type." % embed_footer)


@client.command(name='r/', category='Info', description="Get reddit posts")
async def r(ctx,subreddit:str, loop:int=1):
    await reddit_command(ctx, subreddit, loop)


if __name__ == '__main__':
    client.loop.create_task(check_time())
    
    load_dotenv()

    client.run(os.getenv('TOKEN'))
    print("Ended.")