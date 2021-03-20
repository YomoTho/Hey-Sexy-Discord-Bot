import discord
import json
import os
import asyncio
from timeAndDateManager import TimeStats
from datetime import datetime, time
from discord.ext import tasks, commands
from levelingSystem import Leveling_System, Money
from random import randint, choice
from games import TicTacToe
from dotenv import load_dotenv


data_folder = '../data/'


with open(f'{data}config.json') as f:
    d = json.load(f)
    command_prefix = d['prefix']

intents = discord.Intents().all()
client = commands.Bot(command_prefix=command_prefix, intents=intents)


# This class have data of the server, like server, server owner, id & Text Channels, etc

class Data:
    def __init__(self):
        self.server_data = self.get_server_data()
        self.server_id = self.server_data['server_id']
        self.server_owner_id = self.server_data['owner_id']
        self.channels_id = self.get_channels_id()

    def get_channels_id(self):
        return [channel for channel in self.server_data['channels']]


    def get_useful_role(self, cname):
        with open(f"{data_folder}shop.json") as f:
            shop = json.load(f)
        for role in shop['roles']:
            if shop['roles'][role]['cname'] == cname:
                guild = self.get_server()
                return discord.utils.get(guild.roles, id=int(role))


    def get_server_data(self):
        with open(f'{data_folder}data.json') as f:
            return json.load(f)

    def save_data(self, _data):
        with open(f'{data_folder}data.json', 'w') as f:
            json.dump(_data, f, indent=2)

    def get_useful_channel(self, cname):
        return client.get_channel(int([channel_id for channel_id in self.channels_id if self.server_data['channels'][str(channel_id)]['cname'] == cname][0]))
        
    def get_server(self, get_id=False):
        _server = client.get_guild(int(self.server_id))
        return _server

    def get_owner(self, get_id=False):
        return client.get_user(int(self.server_owner_id)) if get_id == False else int(self.server_owner_id)


class Send_Message(Data):
    def __init__(self, msg):
        self.server_id = server.id
        self.msg = msg
        self.channels_id = data.channels_id; self.server_data = data.server_data
        
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


class CountMessages(Data):
    def __init__(self, func):
        self.func = func 
        self.server_id = data.server_id
        self.data = self.get_server_data()
        self.num_msg = self.data['total_messages']

    def __call__(self):
        self.num_msg += 1
        self.data['total_messages'] = self.num_msg
        self.save_data(self.data)
        return self.func()


# Global variables

data = Data()
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
        
        current_time = datetime.now().strftime('%H:%M')
        current_time = str(current_time).split(':')
        server_stats_alarm = str(server_stats_alarm).split(':')[:-1]
        current_h, current_m = int(current_time[0]), int(current_time[1])
        server_stats_alarm_h, server_stats_alarm_m = int(server_stats_alarm[0]), int(server_stats_alarm[1])
        h_left = server_stats_alarm_h - current_h; m_left = server_stats_alarm_m - current_m
                
        total_seconds = ((h_left * 60) * 60) + (m_left * 60)

        guild = client.get_guild(int(data.server_id))
        
        if current_time == server_stats_alarm:
            time_stats = TimeStats()
            stats_msg = await get_tday_data(time_stats)

            stats_embed = discord.Embed(
                title=f"{str(time_stats.current_date)}",
                description=stats_msg,
                color=discord.Color.blue()
            )
            stats_embed.set_thumbnail(url=guild.icon_url)
            
            channel = data.get_useful_channel(cname='ss')
            
            await channel.send(embed=stats_embed)
            total_seconds = ((24 * 60) * 60)
        else:
            total_seconds = ((h_left * 60) * 60) + (m_left * 60)
        
        await asyncio.sleep(total_seconds / 2)
    


@CountMessages
async def count(): pass


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
            embed = discord.Embed(title=message.content, color=discord.Color.blue())
            embed.set_footer(text=message.author.id)
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            await server_owner.send(embed=embed)
    else:
        if not message.author.bot:
            # await count()
            stats = TimeStats(); stats.on_message()
            user_rank_data = Leveling_System(message.author) # This is doing the leveling system thing
            leveled_up = user_rank_data + int(len(message.content) / 1.5)
            if leveled_up[0]:
                leveled_up_msg = f"**{leveled_up[1] if leveled_up[3] < 10 else leveled_up[1].mention}** has level up from {leveled_up[2]} -> **{leveled_up[3]}**"
                lu_msg = Send_Message(leveled_up_msg)
                await lu_msg.text_channel(cname='lu')
            bot_access_role = data.get_useful_role('ba')
            if bot_access_role in message.author.roles or message.content.startswith(';buy') or message.content.startswith(';rank') or message.content.startswith(';help'):
                await client.process_commands(message)
            


@client.event
async def on_member_join(member):
    new_member = Leveling_System(member)
    new_member.add_user()
    stats = TimeStats()
    stats.member_join()

    welcome_channel = data.get_useful_channel('w')
    if member.bot:
        bot_role = discord.utils.get(member.guild.roles, id=820084294361415691) # TODO make it so Data class can return roles
        await member.add_roles(bot_role)
    else:
        human_role = discord.utils.get(member.guild.roles, id=821839747520528404)
        await member.add_roles(human_role)

    embed = discord.Embed(
        title=f"Welcome {member} to {member.guild}",
        description=f"To know more of the leveling system and that, read it in 'about'." if not member.bot else "This is a bot.",
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


@client.event
async def on_raw_reaction_add(payload : discord.RawReactionActionEvent):
    try:
        if payload.message_id == ttt_game.game_msg.id and not payload.user_id == client.user.id:
            if ttt_game.count <= 9 and not ttt_game.someone_won:
                if payload.user_id == ttt_game.player_1.id and ttt_game.turn.id == payload.user_id: # Player 1
                    await ttt_game.move(payload.emoji)
                elif payload.user_id == ttt_game.player_2.id and ttt_game.turn.id == payload.user_id: # Player 2
                    await ttt_game.move(payload.emoji)
    except NameError:
        pass


#UP HERE ALL THE @client.event ^^ 

###################################

#DOWN HERE IS ALL THE COMMANDS \/ @client.command()


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
async def embed(ctx): # Here i test my embed messages 
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
    
    await ctx.send(embed=stats_embed)



@client.command()
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


@dm.error
async def dm_error(ctx, error):
    print(error)
    await ctx.message.add_reaction('❌')


@client.command(aliases=['cls_dm'])
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
        try:
            leveling_System = Leveling_System(member)
            msg = leveling_System.rank()
        except Exception as e:
            error_embed = discord.Embed(description=f"❗{str(e)}❗", color=discord.Color.from_rgb(255, 0, 0))
            await ctx.send(embed=error_embed)
        else:
            embed = discord.Embed(
                description=f'{msg[1]}  {msg[2]}',
                color=discord.Color.blue()
            )
            embed.add_field(name=msg[3], value=msg[0])
            embed.set_author(name=member, icon_url=member.avatar_url)
            await ctx.send(embed=embed)
    else:
        await ctx.send(f"Bots don't have a rank.")

@rank.error
async def rank_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.message.add_reaction('⁉')
    else:
        print(error)


@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount + 1)

@clear.error 
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify an amount of messages to delete.")


@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.message.add_reaction('🦶🏽')
    await ctx.send(f'**{member}** kicked!')

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, discord.ext.commands.MemberNotFound):
        await ctx.message.add_reaction('❓')
        await ctx.send(f"Huh, Who?")


@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    bans_says = ['**{}** is banned from this server.', 'Yes! That poes **{}** is banned from this server!']
    await member.ban(reason=reason)
    await ctx.message.add_reaction('✅')
    await ctx.send(choice(bans_says).format(member))

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, discord.ext.commands.MemberNotFound):
        await ctx.message.add_reaction('❓')
        await ctx.send(f"Huh, Who?")


@client.command()
async def bans(ctx):
    banned_users = await ctx.guild.bans()
    if len(banned_users) > 0:
        embed = discord.Embed(title=f'{len(banned_users)} Banned Member(s)', color=discord.Color.red())
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

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument): pass # Just do nothing.


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')


@client.command()
async def buy(ctx, *args):
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
                try:
                    buyer = Money(ctx.author)
                    if buyer.buy(roles if args[0] == 'roles' else role):
                        await ctx.message.add_reaction('✅')
                        await ctx.author.add_roles(role)
                    else:
                        await ctx.send(f"You don't have enough money to buy this role.")
                except Exception as e:
                    await ctx.message.add_reaction('❌')
                    await ctx.send(e)
        else:
            raise IndexError
    except IndexError:
        await ctx.send("Not like that, type in: ';buy role {@role}' (e.p ';buy role <@&818591361837695010>')")


@client.command()
async def sell(ctx, *args):
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


@client.command()
async def msg_count(ctx):
    await ctx.send(f"Total message's: {data.get_server_data()['total_messages']}")


@client.command()
async def info(ctx, member : discord.Member=None):
    if member == None: member = ctx.author

    created = member.created_at.strftime(f"%A, %B %d %Y @ %H:%M %p")
    joined = member.joined_at.strftime(f"%A, %B %d %Y @ %H:%M %p")
    roles = member.roles
    roles = ' '.join(a.mention for a in roles[::-1] if not a.name == '@everyone')

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


@client.command()
async def tictactoe(ctx, player1 : discord.Member, player2 : discord.Member):
    if player1.bot:
        await ctx.send(f'{player1} is a bot,  bots cannot play.')
        return
    elif player2.bot:
        await ctx.send(f'{player2} is a bot,  bots cannot play.')
        return
    
    global ttt_game
    ttt_game = TicTacToe(player1, player2)

    game_msg = await ctx.send(await ttt_game.print())
    ttt_game.game_msg = game_msg
    
    for emoji in ttt_game.reactions:
        await game_msg.add_reaction(emoji=emoji)

    embed = discord.Embed(description=f"**{ttt_game.turn.name}** turn")

    wtit = await ctx.send(embed=embed) # 'wtit' stands for 'whos turn is it'
    ttt_game.whos_turn_msg = wtit
    
    
    
@client.command()
@commands.has_permissions(kick_members=True)
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



if __name__ == '__main__':
    client.loop.create_task(check_time())
    
    load_dotenv()
    
    client.run(os.getenv('BT_TOKEN'))
