import discord
import json
import os
from random import randint
from keep_alive import keep_alive
from discord.ext import tasks, commands


intents = discord.Intents().all()
client = commands.Bot(command_prefix='$', intents=intents)

reactions_data_file_name = 'reactions_data.json'

leaving_list = [
    'Aaa, that sexy **{}** left this server :(', 
    '**{}** left this server.', 
    'Oh ya! That ugly **{}** left this server!', 
    'Uhhhh, why did **{}** left this server?!? Tell me why!?',
    'Sooo guys... **{}** has left this server.',
    'Somebody please ask **{}** why he left this server.',
    "It's so disappointing to see that **{}** left this server."
]

girls_role_id = 814994777987874847
gamerGrills_role_id = 814998584645910540
boys_role_id = 814994952785362974
gamer_role_id = 815001323799183391
noobs_role_id = 814994515312115732


@client.event
async def on_ready():
    print(f'{client.user} is online.')
    await check_members_roles()
    await bot_status_loop.start()


@client.event
async def on_member_update(before, after):
    await bot_status()


@client.event
async def on_member_join(member):
    if not member.bot:
        noobs_role = discord.utils.get(member.guild.roles, id=noobs_role_id)
        await member.add_roles(noobs_role)
    else:
        bot_role = discord.utils.get(member.guild.roles, id=814995403115724800)
        await member.add_roles(bot_role) 
    print(f"{member} has joined the {member.guild}.")

    reaction_roles = client.get_channel(815002661526962237)
    welcome_channel = client.get_channel(815178446949842955)
    owner = client.get_user(275192642101313536)
    embed = discord.Embed(
        title=f"Welcome {member} to {member.guild}",
        description=f"To able to do more in this server you need to react in {reaction_roles.mention}",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'{member.guild} • owner: {owner}')
    embed.set_thumbnail(url=member.avatar_url)
    await welcome_channel.send(member.mention, embed=embed)


@client.event
async def on_member_remove(member):
    general = client.get_channel(347364869357436941)
    await general.send(leaving_list[randint(0, len(leaving_list) - 1)].format(member))


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')


@tasks.loop(minutes=10.0)
async def bot_status_loop():
    await bot_status()


async def bot_status():
    guild = client.get_guild(347364869357436940)
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
        male_role = discord.utils.get(guild.roles, id=boys_role_id)
        for member in server_members():
            for role in get_roles(member):
                if role == male_role:
                    males += 1
                    break
        await display_status(f"{males} total male's")

    async def total_females():
        females = 0
        female_role = discord.utils.get(guild.roles, id=girls_role_id)
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
        naughty_people_role = discord.utils.get(guild.roles, id=814996086690545695)
        for member in server_members():
            for role in get_roles(member):
                if role == naughty_people_role:
                    horny_people += 1
                    break
        await display_status(f"{horny_people} total horny people")

    async def total_nerds():
        nerds = 0
        nerd_role = discord.utils.get(guild.roles, id=814995649690206209)
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
    await rand_choose[str(randint(1, 10))]()


@client.command()
@commands.has_permissions(administrator=True)
async def embed(ctx):
    reaction_roles = client.get_channel(815002661526962237)
    embed = discord.Embed(
        title=f"Welcome {ctx.author} to {ctx.author.guild}",
        description=f"To able to do more in this server you need to react in {reaction_roles.mention}",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'{ctx.guild} • owner: {ctx.author}')
    embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.send(ctx.author.mention, embed=embed)


async def check_members_roles():
    guild = client.get_guild(347364869357436940)
    boys_role = discord.utils.get(guild.roles, id=boys_role_id)
    girls_role = discord.utils.get(guild.roles, id=girls_role_id)
    gamerGrills_role = discord.utils.get(guild.roles, id=gamerGrills_role_id)
    gamer_role = discord.utils.get(guild.roles, id=gamer_role_id)
    for member in guild.members:
        is_male, is_female, is_gamer, is_gamer_grill = False, False, False, False
        for role in member.roles:
            if role == boys_role:
                is_male = True
            if role == girls_role:
                is_female = True
            if role == gamer_role:
                is_gamer = True
            if role == gamerGrills_role:
                is_gamer_grill = True
        else:
            if is_female and is_male:
                print(f"{member} is a fe man!")
                await member.remove_roles(girls_role)
                await member.send(f"You can't be a female and male. So role '{girls_role}' get removed.")
            if is_female and is_gamer:
                await member.add_roles(gamerGrills_role)
            if is_male and is_gamer_grill:
                await member.remove_roles(gamerGrills_role)
            

@client.event
async def on_raw_reaction_add(payload : discord.RawReactionActionEvent):
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
        #print(f'emoji={emoji} : role_id={role_id} : description={description}')
        reactions_data[emoji] = {}
        reactions_data[emoji]['role'] = {}
        reactions_data[emoji]['role']['id'] = role_id.id
        reactions_data[emoji]['role']['mention'] = role_id.mention
        reactions_data[emoji]['description'] = description
    reaction_msg_list = list()
    for line in reactions_data:
        reaction_msg_line = f"{line} {reactions_data[line]['role']['mention']} {reactions_data[line]['description']}"
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
        with open(reactions_data_file_name, 'w') as f:
            json.dump(real_reactions_data, f, indent=2)

keep_alive()
client.run(os.getenv('MY_SEXY_TOKEN'))