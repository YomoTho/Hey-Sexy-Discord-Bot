import discord
import json
import os
from os import getenv
from random import randint
from keep_alive import keep_alive
from discord.ext import tasks, commands


#TODO: Make leveling system:
    # How higher level they are, they unlock stuff like: roles, and mybe other stuff
    # How to get exp? texting ALOT, invite people, be more active in this server


#TODO: Clean up this python file, make it easy to read

#TODO: Use classes

command_prefix = "$"

intents = discord.Intents().all()
client = commands.Bot(command_prefix=command_prefix, intents=intents)

reactions_data_file_name = 'reactions_data.json'
warnings_file_name = 'warnings.json'

leaving_says = [
    'Aaa, that sexy **{}** left this server :(', 
    '**{}** left this server.', 
    'Oh ya! That ugly **{}** left this server!', 
    'Uhhhh, why did **{}** left this server?!? Tell me why!?',
    'Sooo guys... **{}** has left this server.',
    'Somebody please ask **{}** why he left this server.',
    "It's so disappointing to see that **{}** left this server."
]

# Getting a bunch of IDs in my discord server 
female_role_id = int(getenv("FEMALE_ROLE_ID"))
gamerGrills_role_id = int(getenv("GAMER_GRILL_ROLE_ID"))
male_role_id = int(getenv("MALE_ROLE_ID"))
gamer_role_id = int(getenv("GAMER_ROLE_ID"))
noobs_role_id = int(getenv("NOOBS_ROLE_ID"))
yomotho_id = int(getenv("YOMOTHO_ID"))
bot_role_id = int(getenv("BOT_ROLE_ID"))
nerd_role_id = int(getenv("NERD_ROLE_ID"))
naughty_people_role_id = int(getenv("NAUGHTY_PEOPLE_ROLE_ID"))
server_id = int(getenv("SERVER_ID"))
mute_role_id = int(getenv("MUTE_ROLE_ID"))

guild = client.get_guild(server_id)
status_number = 0

@client.event
async def on_ready():
    print(f'{client.user} is online.')
    await check_members_roles()
    await bot_status_loop.start()


@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author == client.user:
        if message.content.startswith(command_prefix) and message.author.id == yomotho_id: 
            await client.process_commands(message)
            return
        yomotho = client.get_user(yomotho_id)
        embed = discord.Embed(title=message.content, color=discord.Color.blue())
        embed.set_footer(text=message.author.id)
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        await yomotho.send(embed=embed)

    await client.process_commands(message)


@client.event
async def on_member_join(member):
    if not member.bot:
        noobs_role = discord.utils.get(member.guild.roles, id=noobs_role_id)
        await member.add_roles(noobs_role)
    else:
        bot_role = discord.utils.get(member.guild.roles, id=bot_role_id)
        await member.add_roles(bot_role) 
    print(f"{member} has joined the {member.guild}.")

    reaction_roles = client.get_channel(815002661526962237)
    welcome_channel = client.get_channel(815178446949842955)
    owner = client.get_user(yomotho_id)
    embed = discord.Embed(
        title=f"Welcome {member} to {member.guild}",
        description=f"To able to do more in this server you need to react in {reaction_roles.mention}" if not member.bot else "This is a bot.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'{member.guild} • owner: {owner}')
    embed.set_thumbnail(url=member.avatar_url)
    await welcome_channel.send(member.mention, embed=embed)


@client.event
async def on_member_remove(member):
    general = client.get_channel(347364869357436941)
    await general.send(leaving_says[randint(0, len(leaving_says) - 1)].format(member))


@client.event
async def on_member_update(before, after):
    global status_number
    if str(after.status) == 'online' or str(after.status) == 'offline' or str(after.status) == 'idle':
        if int(status_number) == 1:
            await bot_status(set_status=1)
        elif int(status_number) == 11:
            await bot_status(set_status=11)


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')


@tasks.loop(minutes=1.0)
async def bot_status_loop():
    await bot_status()


@client.command(aliases=['new_stat', 'next_status', 'chgstat', 'guild_stats'])
async def new_status(ctx):
    await bot_status()
    await ctx.message.delete()


def return_warnings(user : discord.Member, users=False, r_count=False):
    with open(warnings_file_name) as f:
        warnings = json.load(f)
    if users:
        return warnings
    else:
        return len([warning for warning in warnings[str(user.id)]]) if not warnings == {} else 0


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
@commands.has_permissions(kick_members=True)
async def warn(ctx, user : discord.Member, *, reason=None):
    with open(warnings_file_name) as f:
        warnings = json.load(f)
    
    if not str(user.id) in warnings:
        warnings[str(user.id)] = {}
        warnings[str(user.id)]['reason'] = reason
        with open(warnings_file_name, 'w') as f:
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

    with open(warnings_file_name, 'w') as f:
        json.dump(warnings, f, indent=2)


@client.command()
@commands.has_permissions(kick_members=True)
async def mute(ctx, user : discord.Member):
    mute_role = discord.utils.get(user.guild.roles, id=mute_role_id)
    await user.add_roles(mute_role)


@client.command()
@commands.has_permissions(kick_members=True)
async def unmute(ctx, user : discord.Member):
    mute_role = discord.utils.get(user.guild.roles, id=mute_role_id)
    for role in user.roles:
        if role == mute_role:
            await user.remove_roles(mute_role)
            break


@client.command()
@commands.has_permissions(administrator=True)
async def del_warn(ctx, user : discord.Member):
    with open(warnings_file_name) as f:
        warnings = json.load(f)

    del warnings[str(user.id)]

    with open(warnings_file_name, 'w') as f:
        json.dump(warnings, f, indent=2)
    

@client.command(aliases=['cls_dm'])
async def cls_ur_msg(ctx, amount=0):
    messages = await ctx.history(limit=amount).flatten()
    for msg in messages:
        if msg.author == client.user:
            await msg.delete()


@client.command(aliases=['dm_hist'])
async def dm_history(ctx, user : discord.Member, *, limit=10):
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
        messages_dict[message.id]['author'] = message.author
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


@client.command()
async def dm(ctx, user : discord.Member, *, message):
    if ctx.author.id == yomotho_id:
        await user.send(message)
        await ctx.send("Message send to {}.".format(user))


@dm.error
async def dm_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument.")
    else:
        await ctx.send(error)


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
            await bot_status_loop.cancel()
            await ctx.send("Loop: Stoped")
        else:
            await bot_status_loop.start()
            await ctx.send("Loop: Start")


async def bot_status(set_status=None, all_status=False):
    guild = client.get_guild(server_id)
    def server_members():
        return [member for member in guild.members]

    def get_roles(user):
        return [role for role in user.roles]

    async def display_status(text):
        await client.change_presence(activity=discord.Game(name=text))
        
    async def online_humans():
        online_users = 0
        for member in server_members():
            if str(member.status) == 'online' or str(member.status) == 'idle' or str(member.status) == 'dnd':
                if not member.bot:
                    online_users += 1
        else:
            await display_status(f"{online_users} online humans")

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
    
    async def total_males():
        males = 0
        male_role = discord.utils.get(guild.roles, id=male_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == male_role:
                    males += 1
                    break
        await display_status(f"{males} total male's")

    async def total_females():
        females = 0
        female_role = discord.utils.get(guild.roles, id=female_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == female_role:
                    females += 1
                    break
        await display_status(f"{females} total female's")
    
    async def total_gamers():
        gamers = 0
        gamer_role = discord.utils.get(guild.roles, id=gamer_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == gamer_role:
                    gamers += 1
                    break
        await display_status(f"{gamers} total gamers")

    async def total_horny_people():
        horny_people = 0
        naughty_people_role = discord.utils.get(guild.roles, id=naughty_people_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == naughty_people_role:
                    horny_people += 1
                    break
        await display_status(f"{horny_people} total horny people")

    async def total_nerds():
        nerds = 0
        nerd_role = discord.utils.get(guild.roles, id=nerd_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == nerd_role:
                    nerds += 1
                    break
        await display_status(f"{nerds} total nerds")

    async def total_afk_users():
        await display_status(f"{len([member for member in server_members() if str(member.status) == 'idle'])} total afk people")

    rand_choose = {
        "1": online_humans,
        "2": online_bots,
        "3": total_humans,
        "4": total_members,
        "5": total_bots,
        "6": total_males,
        "7": total_females,
        "8": total_gamers,
        "9": total_horny_people,
        "10": total_nerds,
        "11": total_afk_users 
    }
    global status_number
    if set_status == None:
        status_number = randint(1, 11)
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


@client.command()
@commands.has_permissions(administrator=True)
async def embed(ctx):                           # Here I test my embed message's
    embed = discord.Embed(
        title=f"**⚠️ !!! YOU HAVE BEEN WARN !!!** ⚠️",
        description=f"Reason: **Testing**",
        color=discord.Color.red()
    )
    embed.set_footer(text=f'{ctx.guild} • owner: {ctx.author}')
    await ctx.send(embed=embed)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embe=discord.Embed(title="<:redcross:781952086454960138>Error", description="**Insufficient permissions!**", color=0x7289da)
        await ctx.send(embed=embe)
    else:
        print(error)


async def check_members_roles():
    guild = client.get_guild(server_id)
    boys_role = discord.utils.get(guild.roles, id=male_role_id)
    girls_role = discord.utils.get(guild.roles, id=female_role_id)
    gamerGrills_role = discord.utils.get(guild.roles, id=gamerGrills_role_id)
    gamer_role = discord.utils.get(guild.roles, id=gamer_role_id)
    naughty_girl_role = discord.utils.get(guild.roles, id=817503056580444180)
    naughty_people_role = discord.utils.get(guild.roles, id=814996086690545695)
    for member in guild.members:
        is_male, is_female, is_gamer, is_gamer_grill, is_naughty = False, False, False, False, False
        for role in member.roles:
            if role == boys_role:
                is_male = True
            if role == girls_role:
                is_female = True
            if role == gamer_role:
                is_gamer = True
            if role == gamerGrills_role:
                is_gamer_grill = True
            if role == naughty_people_role:
                is_naughty = True
        else:
            if is_female and is_male:
                print(f"{member} is a fe man!")
                await member.remove_roles(girls_role)
                await member.send(f"You can't be a female and male. So role '{girls_role}' get removed.")
            if is_female and is_gamer:
                await member.add_roles(gamerGrills_role)
            if is_male and is_gamer_grill:
                await member.remove_roles(gamerGrills_role)
            if is_female and is_naughty:
                print(f'{member} is a naughty girl')
                await member.add_roles(naughty_girl_role)
            

@client.event
async def on_raw_reaction_add(payload : discord.RawReactionActionEvent):
    global guild
    if payload.channel_id == 815002661526962237:
        with open(reactions_data_file_name) as f:
            reaction_data = json.load(f)
        if str(payload.message_id) in reaction_data:
            if str(payload.emoji) in reaction_data[str(payload.message_id)]:
                role_id = reaction_data[str(payload.message_id)][str(payload.emoji)]['role']['id']
                guild = client.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, id=role_id)
                if not payload.member == None:
                    await payload.member.add_roles(role)
                    print(f"{payload.member} has reacted and given the role: {role}.")
                else:
                    print('Payload.member return {}.'.format(payload.member))
        await check_members_roles()
        noobs_role = discord.utils.get(guild.roles, id=noobs_role_id)
        for role in payload.member.roles:
            if role == noobs_role:
                await payload.member.remove_roles(noobs_role)
                break
    elif payload.channel_id == 735637767131889704: # Rules channel ID
        print(f"{payload.member} reacted in rules: {payload.emoji}")
    else:
        print(f"{payload.member} has reacted ", payload.channel_id)


@client.event
async def on_raw_reaction_remove(payload : discord.RawReactionActionEvent):
    if payload.channel_id == 815002661526962237:
        with open(reactions_data_file_name) as f:
            reaction_data = json.load(f)
        if str(payload.message_id) in reaction_data:
            if str(payload.emoji) in reaction_data[str(payload.message_id)]:
                role_id = reaction_data[str(payload.message_id)][str(payload.emoji)]['role']['id']
                guild = client.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, id=role_id)
                for member in guild.members:
                    if member.id == payload.user_id:
                        await member.remove_roles(role)
                        print(f"{member} has removed react: {role}")
                        break
        await check_members_roles()
    elif payload.channel_id == 735637767131889704: # Rules channel ID
        print(f"{payload.member} removed reaction in rules: {payload.emoji}")
    else:
        print(f"{payload.member} has removed reacted ", payload.channel_id)


@client.command()
@commands.has_permissions(administrator=True)
async def add_react(ctx, channel, *, reaction_ctx):
    to_send = client.get_channel(int(channel))
    reactions = reaction_ctx.split(' / ')
    with open(reactions_data_file_name) as f:
        real_reactions_data = json.load(f)
    reactions_data = dict()
    msg_id = str()
    for reaction in reactions:
        reaction_block = reaction.split(' ')
        emoji = reaction_block[0]
        role_id = reaction_block[1]
        for role in ctx.guild.roles:
            if role_id == role.mention:
                role_id = role
        if len(reaction_block) > 2:
            description = reaction_block[2:]
            description = ' '.join(description)
        else:
            description = ''
        reactions_data[emoji] = {}
        reactions_data[emoji]['role'] = {}
        reactions_data[emoji]['role']['id'] = role_id.id
        reactions_data[emoji]['role']['mention'] = role_id.mention
        reactions_data[emoji]['description'] = description
    reaction_msg_list = list()
    for line in reactions_data:
        reaction_msg_line = f"{line} {reactions_data[line]['description']}"
        reaction_msg_list.append(reaction_msg_line)
        reaction_msg = '\n'.join(reaction_msg_list)
    else:
        embed = discord.Embed(
            title='React to this to get roles.',
            description=reaction_msg,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f'{ctx.guild} • owner: {ctx.author}')
        embed.set_thumbnail(url=ctx.guild.icon_url)
        msg = await to_send.send(embed=embed)
        for _emoji in reactions_data:
            await msg.add_reaction(_emoji)
        msg_id = msg.id
        real_reactions_data[msg_id] = reactions_data
        if int(channel) == 815002661526962237:
            with open(reactions_data_file_name, 'w') as f:
                json.dump(real_reactions_data, f, indent=2)

keep_alive()
client.run(os.getenv('MY_SEXY_TOKEN'))