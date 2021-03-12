import discord
import json
import os
from discord.ext import tasks, commands
from levelingSystem import Leveling_System
from random import randint


command_prefix = ";"

intents = discord.Intents().all()
client = commands.Bot(command_prefix=command_prefix, intents=intents)


data_folder = '../data/'


# This class have data of the server, like server, server owner, id & Text Channels, etc
class Data:
    def __init__(self, server_id, server_owner_id):
        self.server_id = server_id
        self.server_owner_id = server_owner_id
        self.server_data = self.get_server_data()
        self.channels_id = self.get_channels_id()

    def get_channels_id(self):
        return [channel for channel in self.server_data[str(self.get_server(get_id=True))]['channels']]

    def get_server_data(self):
        with open(f'{data_folder}data.json') as f:
            return json.load(f)

    def get_useful_channel(self, cname):
        return client.get_channel(int([channel_id for channel_id in self.channels_id if self.server_data[str(self.server_id)]['channels'][channel_id]['cname'] == cname][0]))
        
    def get_server(self, get_id=False):
        return client.get_guild(self.server_id) if get_id == False else self.server_id

    def get_owner(self, get_id=False):
        return client.get_user(self.server_owner_id) if get_id == False else self.server_owner_id


class Send_Message(Data):
    def __init__(self, msg):
        self.server_id = data.server_id
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



# Global variables

data = None
status_number = 0


# FROM HERE DOWN, WILL BE NORMAL/CUSTOM FUNCTION'S


def store_data():
    for guild in client.guilds:
        if guild.name == 'Sexy People':
            server_id = guild.id
            server_owner_id = guild.owner.id
        break
    global server_owner, server, data
    data = Data(server_id, server_owner_id)
    #data.server_id = server_id; data.server_owner_id = server_owner_id
    server_owner = data.get_owner()
    server = data.get_server()


async def bot_status(set_status=None, all_status=False):
    guild = client.get_guild(int(data.server_id))
    def server_members():
        return [member for member in guild.members]

    #def get_roles(user):
        #return [role for role in user.roles]

    async def display_status(text):
        await client.change_presence(activity=discord.Game(name=text))
        
    async def online_humans():
        online_users, afk_users = 0, 0
        for member in server_members():
            if str(member.status) == 'online' or str(member.status) == 'dnd':
                if not member.bot:
                    online_users += 1
            elif str(member.status) == 'idle' and not member.bot:
                afk_users += 1
        else:
            await display_status(f"{online_users} online humans" if afk_users == 0 else f"{online_users} online humans, {afk_users} afk")

    async def online_bots():
        online_users = 0
        for member in server_members():
            if str(member.status) == 'online' or str(member.status) == 'idle' or str(member.status) == 'dnd':
                if member.bot:
                    online_users += 1
        else:
            await display_status(f"{online_users} online bots")

    async def total_humans():
        await display_status(f"{len([human for human in server_members() if not human.bot])} total humans")
    
    async def total_members():
        await display_status(f"{len([member for member in server_members()])} total members")

    async def total_bots():
        await display_status(f"{len([_bot for _bot in server_members() if _bot.bot])} total bots")

    async def total_afk_users():
        await display_status(f"{len([member for member in server_members() if str(member.status) == 'idle'])} total afk people")

    rand_choose = {
        "1": online_humans,
        "2": online_bots,
        "3": total_humans,
        "4": total_members,
        "5": total_bots,
        "6": total_afk_users 
    }
    global status_number
    if set_status == None:
        status_number = randint(1, len([f for f in rand_choose]))
    else: status_number = set_status
    if not all_status:
        await rand_choose[str(status_number)]()
    else:
        all_s = list()
        for s in rand_choose:
            func = str(rand_choose[str(s)])
            func = func.split("<function bot_status.<locals>.")
            func = func[1].split(' ')
            all_s.append(f"{s} {func[0]}")
        all_s = '\n'.join(all_s)
        return all_s 


# FORM HERE DOWN, THIS IS THE @client.event & @tasks functions


@client.event
async def on_ready():
    print(f"{client.user} is online.")
    store_data()
    bot_status_loop.start()


@tasks.loop(minutes=1.0)
async def bot_status_loop():
    await bot_status()

    
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
            user_rank_data = Leveling_System(message.author) # This is doing the leveling system thing
            leveled_up = user_rank_data + int(len(message.content) / 1.5)
            if leveled_up[0]:
                leveled_up_msg = f"**{leveled_up[1] if leveled_up[3] < 10 else leveled_up[1].mention}** has level up from {leveled_up[2]} -> **{leveled_up[3]}**"
                lu_msg = Send_Message(leveled_up_msg)
                await lu_msg.text_channel(cname='lu')

            await client.process_commands(message)


@client.event
async def on_member_join(member):
    new_member = Leveling_System(member)
    new_member.add_user()


@client.event
async def on_member_remove(member):
    noob = Leveling_System(member)
    await noob.remove_user()


@client.event
async def on_member_update(before, after):
    global status_number
    if str(after.status) == 'online' or str(after.status) == 'offline' or str(after.status) == 'idle':
        if int(status_number) == 1:
            await bot_status(set_status=1)
        elif int(status_number) == 11:
            await bot_status(set_status=6)



#UP HERE ALL THE @client.event ^^ 

###################################

#DOWN HERE IS ALL THE COMMANDS \/ @client.command()



@client.command()
async def test(ctx): # Here I do my test commands
    pass 


@client.command()
async def set_status(ctx, status_num):
    await bot_status(set_status=status_num)


@client.command()
async def all_status(ctx):
    await ctx.send(await bot_status(all_status=True))


@client.command()
async def status_settings(ctx, agru): # TODO: Make status settings, make it so it can disable/enable status, stay, loop time, etc
    if agru.startswith('hold='):
        agru = agru.split('=')
        if agru[1] == 'True':
            await ctx.send("Loop: Stoped")
            await bot_status_loop.cancel()
        elif agru[1] == 'False':
            await ctx.send("Loop: Start")
            await bot_status_loop.start()


@client.command(aliases=['new_stat', 'next_status', 'chgstat', 'guild_stats'])
async def new_status(ctx):
    await bot_status()
    await ctx.message.delete()


@client.command()
async def dm(ctx, user : discord.Member, *, msg):
    msg_cmd = ctx.message
    if ctx.author.id == data.server_owner_id:
        to = Send_Message(msg); await to.dm(user)
        await msg_cmd.add_reaction('✅')
    else:
        await msg_cmd.add_reaction('⛔')

@dm.error
async def dm_error(ctx, error):
    await ctx.message.add_reaction('❌')
    await ctx.send(error)


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
        leveling_System = Leveling_System(member)
        try:
            msg = leveling_System.rank()
        except Exception as e:
            error_embed = discord.Embed(description=f"❗{str(e)}❗", color=discord.Color.from_rgb(255, 0, 0))
            await ctx.send(embed=error_embed)
        else:
            embed = discord.Embed(
                title=str(member),
                description=f'{msg[1]}  {msg[2]}',
                color=discord.Color.blue()
            )
            embed.add_field(name=msg[3], value=msg[0])
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
    amount += 1
    await ctx.channel.purge(limit=amount)

# 'clear' command error
@clear.error 
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify an amount of messages to delete.")


@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member} got kicked.')


@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member} is banned from this server.')


@client.command()
async def bans(ctx):
    banned_users = await ctx.guild.bans()
    if len(banned_users) > 0:
        for ban_usr in banned_users:
            await ctx.send(ban_usr)
    else:
        await ctx.send('There are nobody banned from this server.')


@client.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'{user} is now unbanned.')
            return


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')




client.run("ODE2NjY4NjA0NjY5NzU1NDMz.YD-T6A.elZITTn8GRX1sOHRUbSWzME3aH4")
