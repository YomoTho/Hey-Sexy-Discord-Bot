import discord
import json
import os
from keep_alive import keep_alive
from discord.ext import commands


intents = discord.Intents().all()
client = commands.Bot(command_prefix='$', intents=intents)

reactions_data_file_name = 'reactions_data.json'

girls_role_id = 814994777987874847
gamerGrills_role_id = 814998584645910540
boys_role_id = 814994952785362974
gamer_role_id = 815001323799183391


@client.event
async def on_ready():
    print(f'{client.user} is online.')
    await check_members_roles()


@client.command()
async def ping(ctx):
    await ctx.send(f'ping {round(client.latency * 1000)}ms')


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