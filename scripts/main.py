import discord
import json
import os
import asyncio
import pytz
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


with open(f'{data_folder}config.json') as f:
    d = json.load(f)
    command_prefix = d['prefix']

intents = discord.Intents().all()
client = commands.Bot(command_prefix=command_prefix, intents=intents)
#client.remove_command('help')


# This class have data of the server, like server, server owner, id & Text Channels, etc

class Send_Message(Data):
    def __init__(self, msg):
        self.server_id = server.id
        self.msg = msg
        self.channels_id = data.channels_id; self.server_data = data.server_data
        self.client = client
        
    async def dm(self, to : discord.Member):
        await to.send(self.msg)
        
    async def text_channel(self, cname=None, _channel_id=None):
        if not cname == None:
            to = self.get_useful_channel(cname)
            await to.send(self.msg)
        elif not _channel_id == None:
            to = client.get_channel(int(_channel_id))
            await to.send(self.msg)
        else:
            raise Exception


# Global variables

data = Data(client)
status_number = 0
server = None
server_owner = None

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
    with open(f'{data_folder}warnings.json') as f:
        warnings = json.load(f)
    if users:
        return warnings
    else:
        return len([warning for warning in warnings[str(user.id)]]) if not warnings == {} else 0

    
async def check_time():
    await client.wait_until_ready()
    await asyncio.sleep(1)
    
    while client.is_closed:     # TODO : Clean this code
        server_stats_alarm = time(hour=23, minute=59)
        
        sa_timezone = pytz.timezone('Africa/Johannesburg')
        
        current_time = datetime.now(sa_timezone).strftime('%H:%M')
        current_time = str(current_time).split(':')
        server_stats_alarm = str(server_stats_alarm).split(':')[:-1]
        current_h, current_m = int(current_time[0]), int(current_time[1])
        server_stats_alarm_h, server_stats_alarm_m = int(server_stats_alarm[0]), int(server_stats_alarm[1])
        h_left = server_stats_alarm_h - current_h; m_left = server_stats_alarm_m - current_m
        
        total_seconds = ((h_left * 60) * 60) + (m_left * 60)

        print('S:', total_seconds)

        guild = client.get_guild(int(data.server_id))
        
        if current_time == server_stats_alarm:
            time_stats = TimeStats()
            stats_msg = await get_tday_data(time_stats)
            guild = client.get_guild(int(data.server_id))
            
            stats_embed = discord.Embed(
                title=f"{str(time_stats.current_date)}",
                description="This will show the server stats of this date.",
                color=discord.Color.blue()
            )
            stats_embed.add_field(name='Members', value=f"Total members: **{stats_msg[0]}**\nTotal humans: **{stats_msg[1]}**\nTotal bots **{stats_msg[2]}**", inline=False)
            
            stats_embed.add_field(name='Joins/leaves', value=f"Members joined: **{stats_msg[3]}**\nTotal leaves: **{stats_msg[4]}**", inline=False)
            
            stats_embed.add_field(name='Messages', value=f"Today total messages: **{stats_msg[5]}**", inline=False)
            stats_embed.set_thumbnail(url=guild.icon_url)
            stats_embed.set_footer(text=f'{guild} • Created_at: {guild.created_at}')
            
            channel = data.get_useful_channel(cname='ss')
            
            await channel.send(embed=stats_embed)
            total_seconds = ((24 * 60) * 60)
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


# FORM HERE DOWN, THIS IS THE @client.event & @tasks functions

@client.event
async def on_ready():
    print(f"{client.user} is online.")
    await store_data()
    

    
@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        if not message.author.bot:
            if message.content.startswith(command_prefix) and message.author.id == server_owner.id:
                await client.process_commands(message)
                return
            
            if message.content.startswith('https://tenor.com/'):
                msg = f"From {message.author}\n{message.content}\n{message.author.id}"
                await server_owner.send(msg)
            else:
                embed = discord.Embed(title=message.content, color=discord.Color.blue())
                embed.set_footer(text=message.author.id)
                embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                await server_owner.send(embed=embed)
    else:
        if not message.author.bot:
            stats = TimeStats(); stats.on_message()
            user_rank_data = Leveling_System(message.author) # This is doing the leveling system thing
            leveled_up = user_rank_data + int(len(message.content) / 1.5)
            if leveled_up[0]:
                leveled_up_msg = f"**{leveled_up[1] if leveled_up[3] < 20 else leveled_up[1].mention}** has level up from {leveled_up[2]} -> **{leveled_up[3]}**"
                lu_msg = Send_Message(leveled_up_msg)
                await lu_msg.text_channel(cname='lu')
            bot_access_role = data.get_role(cname='ba')
            if bot_access_role in message.author.roles or message.content.startswith(';buy') or message.content.startswith(';rank') or message.content.startswith(';help'):
                await client.process_commands(message)
                #await update_live_rank(message.author)
                await user_rank_data.update_live_rank(data)


@client.event
async def on_member_join(member):
    new_member = Leveling_System(member)
    new_member.add_user()
    stats = TimeStats()
    stats.member_join()

    welcome_channel = data.get_useful_channel('w')
    leveling_system_channel = data.get_useful_channel('ls')
    if member.bot:
        await member.add_roles(data.get_role('bots'))
    else:
        await member.add_roles(data.get_role('humans'))

    embed = discord.Embed(
        title=f"Welcome {member.name} to {member.guild}",
        description=f"To know more of the leveling system and that, read it in {leveling_system_channel.mention}" if not member.bot else "This is a bot.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'{member.guild}')
    embed.set_thumbnail(url=member.avatar_url)
    await welcome_channel.send(member.mention, embed=embed)


@client.event
async def on_member_remove(member):
    noob = Leveling_System(member)
    noob.remove_user()
    stats = TimeStats()
    stats.member_leave()
    print(f"{member} has left the server.")


@client.event
async def on_raw_reaction_add(payload : discord.RawReactionActionEvent):
    if not payload.user_id == client.user.id:
        if payload.emoji.name == '❌':
            with open(f"{data_folder}errors.json") as f:
                errors_data = json.load(f)
            
            if str(payload.channel_id) in errors_data:
                if str(payload.message_id) in errors_data[str(payload.channel_id)]:
                    dumb_user = client.get_user(errors_data[str(payload.channel_id)][str(payload.message_id)]['user_id'])
                    embed = discord.Embed(title=" :x: Error", color=0xff001c)
                    embed.set_author(name=dumb_user, icon_url=dumb_user.avatar_url)
                    embed.add_field(name='Message:', value=f""""{errors_data[str(payload.channel_id)][str(payload.message_id)]['msg_ctx']}" """, inline=False)
                    embed.add_field(name='Error Message:', value=f"{errors_data[str(payload.channel_id)][str(payload.message_id)]['error']}", inline=False)
                    channel = client.get_channel(payload.channel_id)
                    await channel.send(embed=embed)

                    del errors_data[str(payload.channel_id)][str(payload.message_id)]

                    with open(f"{data_folder}errors.json", 'w') as f:
                        json.dump(errors_data, f, indent=4)
        else:
            try:
                if payload.message_id == ttt_game.game_msg.id and not payload.user_id == client.user.id:
                    if ttt_game.count <= 9 and not ttt_game.someone_won:
                        if payload.user_id == ttt_game.player_1.id and ttt_game.turn.id == payload.user_id: # Player 1
                            await ttt_game.move(payload.emoji)
                        elif payload.user_id == ttt_game.player_2.id and ttt_game.turn.id == payload.user_id: # Player 2
                            await ttt_game.move(payload.emoji)
                elif not ttt_game.whos_turn_msg is None:
                    if payload.message_id == ttt_game.whos_turn_msg.id and not payload.user_id == client.user.id:
                        await tictactoe(ctx=ttt_game.ctx, player1=ttt_game.player_1, player2=ttt_game.player_2)
            except NameError:
                pass
    
    
@client.event
async def on_command_error(ctx, error):
    with open(f'{data_folder}errors.json') as f:
        errors_data = json.load(f)

    await ctx.message.add_reaction('❌')

    if not str(ctx.channel.id) in errors_data:
        errors_data[str(ctx.channel.id)] = {}
    errors_data[str(ctx.channel.id)][str(ctx.message.id)] = {}
    errors_data[str(ctx.channel.id)][str(ctx.message.id)]['error'] = str(error)
    errors_data[str(ctx.channel.id)][str(ctx.message.id)]['msg_ctx'] = ctx.message.content
    errors_data[str(ctx.channel.id)][str(ctx.message.id)]['user_id'] = ctx.author.id

    with open(f'{data_folder}errors.json', 'w') as f:
        json.dump(errors_data, f, indent=4)
    


#UP HERE ALL THE @client.event ^^ 


#########################################################

#########################################################


#DOWN HERE IS ALL THE COMMANDS \/ @client.command()


@client.command()
@commands.is_owner()
async def test(ctx): # Here i test commands
    await ctx.send('test')


@client.command(pass_context=True)
async def join(ctx):
    if ctx.author.voice:
        voice_channel = ctx.author.voice
        await voice_channel.channel.connect()
    else:
        await ctx.send("You not in a voice channel.")


@client.command(pass_context=True, aliases=['leave'])
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


@client.command()
@commands.is_owner()
async def embed(ctx, *, args): # Here i test my embed messages 
    embed_msgs = args.split(' \ ')
    
    embed = discord.Embed(
        title=embed_msgs[0] if not embed_msgs[0] == 'None' else ' ',
        description=embed_msgs[1] if not embed_msgs[1] == 'None' else ' '
        )
    await ctx.send(embed=embed)



@client.command()
@commands.is_owner()
async def dm(ctx, *args):
    if args[0] in ['history', 'hist']:
        async def hist(user : discord.Member, limit=10):
            messages_from_user = await user.history(limit=limit).flatten()
            embed = discord.Embed(
                title='DM History',
                color=discord.Color.blue()
            )
            embed.set_author(name=user, icon_url=user.avatar_url)
            messages_dict = dict()
            for message in messages_from_user:
                messages_dict[message.id] = {}
                messages_dict[message.id]['content'] = message.content
                messages_dict[message.id]['author'] = f'{message.author} [ msg id: {message.id} ]' if message.author.id == client.user.id else message.author
            else:
                messages_author = list()
                messages_content = list()
                for message in messages_dict:
                    messages_author.append(messages_dict[message]['author'])
                    messages_content.append(messages_dict[message]['content'])
                else:
                    messages_author = messages_author[::-1]; messages_content = messages_content[::-1]
                    for index, message in enumerate(messages_content):
                        embed.add_field(name=messages_author[index], value=message, inline=False)
                    await ctx.send(embed=embed)
        try: _limit = int(args[2])
        except IndexError: _limit = 10
        await hist(client.get_user(int(args[1][3:-1] if args[1].startswith('<@!') else args[1])), _limit)
    elif args[0] in ['del', 'delete']:
        async def delete_messages(user : discord.Member, msg_ids):
            messages = await user.history(limit=50).flatten()
            msg_cmd = ctx.message
            right_messages = list()

            for message in messages:
                right_messages.append([msg_id for msg_id in msg_ids if message.id == int(msg_id)])
            else:
                right_messages = list(filter(lambda a: a != [], right_messages))
                for message in messages:
                    for to_del_msg in right_messages:
                        if message.id == int(to_del_msg[0]):
                            await message.delete()
                else:
                    await msg_cmd.add_reaction('✅')
    
        ids = args[2:]
        user_id = int(args[1][3:-1]) if args[1].startswith('<@!') else int(args[1])
        await delete_messages(client.get_user(user_id), ids)
    else:
        if args[0].startswith('<#'): # Check if it's a channel
            channel_id = int(args[0][2:-1])
            channel = client.get_channel(channel_id)
            await channel.send(' '.join(word for word in args[1:]))
        else:
            user = client.get_user(int(args[0][3:-1] if args[0].startswith('<@!') else args[0]))
            async def dmm(msg):
                msg_cmd = ctx.message
                if ctx.author.id == server_owner.id:
                    to = Send_Message(msg); await to.dm(user)
                    await msg_cmd.add_reaction('✅')
                    if not args[0].startswith('<@!'):
                        await ctx.send(f'To {user}')
                else:
                    await msg_cmd.add_reaction('⛔')
                
            await dmm(' '.join(word for word in args[1:]))



@client.command()
async def set_status(ctx, status_num):
    pass # TODO make it so a user can set the bot status


@client.command(aliases=['cls_dm'])
@commands.is_owner()
async def cls_ur_msg(ctx, amount=50): # This will delete this bot message's
    if ctx.author.id == server_owner.id:
        messages = await ctx.history(limit=amount).flatten()
        for msg in messages:
            if msg.author == client.user:
                await msg.delete()


@client.command()
async def rank(ctx, member : discord.Member=None):
    if member == None:
        member = ctx.author
    if not member.bot:
        user_rank = Leveling_System(member)
        await ctx.send(embed=await user_rank.rank_msg(member))
    else:
        await ctx.send("Bots don't have rank.")


@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount + 1)


@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.message.add_reaction('🦶🏽')
    await ctx.send(f'**{member}** kicked!')


@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    bans_says = ['**{}** is banned from this server.', 'Yes! That poes **{}** is banned from this server!']
    await member.ban(reason=reason)
    await ctx.message.add_reaction('✅')
    await ctx.send(choice(bans_says).format(member))


@client.command()
async def bans(ctx):
    banned_users = await ctx.guild.bans()
    if len(banned_users) > 0:
        embed = discord.Embed(title=f'{len(banned_users)} Banned Member(s)', color=discord.Color.from_rgb(255, 0, 0))
        for ban_usr in banned_users:
            embed.add_field(name=f'{ban_usr.user}  [ ID: {ban_usr.user.id} ]', value=f'Reason: **{ban_usr.reason}**')
        else:
            await ctx.send(embed=embed)
    else:
        await ctx.send('There are nobody banned from this server.')


@client.command()
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

#@unban.error
#async def unban_error(ctx, error):
 #   if isinstance(error, discord.ext.commands.BadArgument): pass # Just do nothing.


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')


@client.command()
async def buy(ctx, *args):
    if ctx.channel == data.get_useful_channel(cname='sh') or ctx.author.id == data.get_owner().id:
        try:
            if args[0] in 'role':
                try:
                    role_id = args[1].replace('<@&', ''); role_id = role_id.replace('>', '')
                    role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                    if role in ctx.author.roles:
                        await ctx.send('You already have this role. lol')
                        return
                except ValueError:
                    if args[1].startswith('<@!'):
                        await ctx.send(f"You can't buy {args[1]}, dum dum")
                    else:
                        await ctx.send(f"Huh, who!?")
                else:
                    buyer = Money(ctx.author)
                    if next(buyer.buy(role=role)):
                        await ctx.message.add_reaction('✅')
                        await ctx.author.add_roles(role)
                    else:
                        await ctx.send(f"You don't have enough money to buy this role.")
            elif args[0] in ['lr', 'liverank']:     # TODO add live rank
                buyer = Money(ctx.author)
                buying = buyer.buy(liverank=1)
                if next(buying):
                    live_rank_channel = data.get_useful_channel(cname='lr')
                    user_rank = Leveling_System(ctx.author)
                    liverank_msg = await live_rank_channel.send(f'{ctx.author.mention} live rank', embed=await user_rank.rank_msg(ctx.author))
                    
                    with open(f'{data_folder}liverank.json', 'r') as f:
                        liverank_users = json.load(f)
                    
                    liverank_users[ctx.author.id] = {}
                    liverank_users[ctx.author.id]['msg_id'] = liverank_msg.id
                    liverank_users[ctx.author.id]['channel_id'] = liverank_msg.channel.id
                    
                    with open(f'{data_folder}liverank.json', 'w') as f:
                        json.dump(liverank_users, f, indent=2)
                        
                    if next(buying):     # Take money
                        await ctx.message.add_reaction('✅')
            else:
                raise IndexError
        except IndexError:
            await ctx.send("Not like that, type in: ';buy role {@role}' (e.p ';buy role <@&818591361837695010>')")
        except Exception as e:
            await ctx.message.add_reaction('❌')
            await ctx.send(e)
    else:
        await ctx.send(f"You can only buy/sell stuff in {data.get_useful_channel(cname='sh').mention}")


@client.command()
async def sell(ctx, *args):
    if ctx.channel == data.get_useful_channel(cname='sh'):
        try:
            if args[0] == 'role':
                try:
                    role_id = args[1].replace('<@&', ''); role_id = role_id.replace('>', '')
                    role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                except ValueError:
                    if args[1].startswith('<@!'):
                        await ctx.send(f"You can't sell {args[1]}, dum dum")
                    else:
                        await ctx.send(f"Huh!?")
                else:
                    try:
                        seller_user = Money(ctx.author) # Here we define the member
                        seller = seller_user.sell(role) # This function is a generator
                        if next(seller): # If the user can sell this role, then it will return True
                            await ctx.author.remove_roles(role)
                            await ctx.message.add_reaction('✅')
                    except Exception as e:
                        await ctx.send(e)
                    else:
                        # If verything went good then it will save, the changes
                        money_update = next(seller) # This will save and return info
                        await ctx.send(f"You had ${money_update[0]}, then sell '{role.name}' for ${money_update[2]}. Now you have $**{money_update[1]}**.")
            else:
                raise IndexError
        except IndexError:
            await ctx.send("Not like that dummy, type in: ';sell role {@role}' \n(e.p: ';sell role <@&818591361837695010>')")
    else:
        await ctx.send(f"You can only buy/sell stuff in {data.get_useful_channel(cname='sh').mention}")


@client.command()
async def msg_count(ctx):
    stats = TimeStats()
    await ctx.send(f"Total message's: {stats.cal_total_messages()}")


@client.command()
async def info(ctx, member : discord.Member=None):
    if member == None: member = ctx.author

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
    
    
@client.command()
async def pfp(ctx, member : discord.Member=None):
    if member == None: member = ctx.author
    await ctx.send(member.avatar_url)
    

@client.command(aliases=['ttt'])
async def tictactoe(ctx, player1, player2 : discord.Member=None):
    if player1 == 'bvb': # This stands for 'Bot vs Bot'
        player1 = client.user
        player2 = client.get_user(816668604669755433) # This ID is local bot
    else:
        if type(player1) is str:
            player1 = ctx.author
        if player2 is None:
            player2 = client.get_user(int(player1[3:-1]))
    
    global ttt_game
    ttt_game = TicTacToe(player1, player2, data, ctx)

    game_msg = await ctx.send(await ttt_game.print())
    ttt_game.game_msg = game_msg
    
    if (player1.bot == False and player2.bot == False) or (not player1.bot or not player2.bot):
        for emoji in ttt_game.reactions:
            await game_msg.add_reaction(emoji=emoji)

    embed = discord.Embed(description=f"**{ttt_game.turn.name}** turn")

    wtit = await ctx.send(embed=embed) # 'wtit' stands for 'whos turn is it'
    ttt_game.whos_turn_msg = wtit
    
    if ttt_game.turn.bot:
        await ttt_game.move(choice(ttt_game.reactions))
    
    
@client.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, user : discord.Member, *, reason=None):
    with open(f'{data_folder}warnings.json') as f:
        warnings = json.load(f)
    
    if not str(user.id) in warnings:
        warnings[str(user.id)] = {}
        warnings[str(user.id)]['reason'] = reason
        with open(f'{data_folder}warnings.json', 'w') as f:
            json.dump(warnings, f, indent=2)
    else:
        warnings[str(user.id)][f'reason{return_warnings(user)}'] = reason

    warning_count_text = f"This is your {return_warnings(user) + 1}th warning"
    reason_text = f"Reason: **{reason}**" if not reason == None else f"Reason: {reason}"
    
    embed = discord.Embed(
        title=f"**⚠️ !!! YOU HAVE BEEN WARN !!!** ⚠️",
        description=f"{reason_text}\n{warning_count_text}" if not return_warnings(user) == 1 else reason_text,
        color=discord.Color.red()
    )
    embed.set_footer(text=f'{ctx.guild} • owner: {ctx.author}')
    await user.send(embed=embed)
    await ctx.send("Warning send.")

    with open(f'{data_folder}warnings.json', 'w') as f:
        json.dump(warnings, f, indent=2)


@client.command(aliases=['warns'])
@commands.has_permissions(administrator=True)
async def warnings(ctx, member : discord.Member=None):
    warnings = return_warnings(member, users=True)
    embed = discord.Embed(
        title=f"Warnings list",
        color=discord.Color.red()
    )
    for warning in warnings:
        reasons_list = list()
        for r_list in warnings[warning]:
            reasons_list.append(str(warnings[warning][r_list]))
        reasons = str(); reasons = '\n• '.join(reasons_list)
        user = client.get_user(int(warning))
        warnings_user = f"**{user}**"
        warning_reason = f"{len(reasons_list)} Reason(s):\n• {reasons}"
        embed.add_field(name=warnings_user, value=warning_reason, inline=False)
    
    await ctx.send(embed=embed)


@client.command()
@commands.has_permissions(administrator=True)
async def del_warn(ctx, user : discord.Member):
    with open(f'{data_folder}warnings.json') as f:
        warnings = json.load(f)

    del warnings[str(user.id)]

    with open(f'{data_folder}warnings.json', 'w') as f:
        json.dump(warnings, f, indent=2)


@client.command(aliases=['server_update', 'announce', '__sa__'])
@commands.has_permissions(administrator=True)
async def server_announcement(ctx, *, msg):
    server_announcement_channel = data.get_useful_channel(cname='sa')
    await server_announcement_channel.send(msg)
    await ctx.message.add_reaction('✅')


@client.command()
async def _help(ctx):
    embed = discord.Embed(title='Commands:', description='Prefix: "**;**"')
    leveling_system_commands = """
    **rank** | Show your rank. ";rank"
    **buy** | You can buy roles ";buy role @role"
    **sell** | You can sell roles ";sell role @role"
    """
    moderations_commands = """
    **ban** | ban members. ";ban [@member] [reason]"
    **bans** | show all banned members. ";bans"
    **unban** | unban members. ";unban [member id]" 
    **kick** | kick members. ";kick [@member] [reason]"
    **warn** | warn members. ";warn [@member] [reason]"
    **warns** | show all the warnings list. ";warns"
    **del_warn** | remove's a member warnings.";del_warn [@member]"
    **clear** | delete message's. ";clear [amount]"
    **dm** | To dm member's (as bot). ";dm [@member] [your message]"
    """
    fun_commands = """
    **ping** | show the bot latency. ";ping"
    **pfp** | show a member profile pic. ";pfp [@member]"
    **info** | show's info of a member. ";info [@member]"
    **msg_count** | show's the total message's. ";msg_count"
    **tictactoe** (ttt) | tic-tac-toe game. ";tictactoe [@member 1] [@member 2]"
    """

    embed.add_field(name='Leveling System:', value=leveling_system_commands, inline=False)
    embed.add_field(name='MOD:', value=moderations_commands, inline=False)
    embed.add_field(name='Fun commands:', value=fun_commands, inline=False)

    await ctx.send(embed=embed)


if __name__ == '__main__':
    client.loop.create_task(check_time())
    
    load_dotenv()
    
    client.run(os.getenv('TOKEN'))
