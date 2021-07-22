import discord
import os
import random
import asyncio
import inspect
import signal
from discord import Color
from discord.ext import commands
from discord.ext.commands.errors import BadArgument, ChannelNotFound, MemberNotFound
from games import TicTacToe
from datetime import datetime
from typing import Union
from my_googlesearch import search
try:
    from scripts.data import Data, MyChannel, Reference
    from scripts.leveling_system import Leveling_System
except ModuleNotFoundError: # I do this, bc then I can see the vscode's auto complete
    from data import Data, MyChannel, Reference
    from leveling_system import Leveling_System



class Bot_Commands:
    class Error(Exception): pass

    def __init__(self, client) -> None:
        self.client = client
        self.reference = Reference(client)


    def command(self, *args, **kwargs):
        return self.client.command(*args, **kwargs)


    async def command_success(self, message:discord.Message) -> None:
        asyncio.create_task(message.add_reaction('✅'))



class Owner_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)

        
        @self.command(help='Command testing')
        @commands.is_owner()
        async def test(ctx:commands.Context, num: str):
            pass


        
        @self.command()
        @commands.is_owner()
        async def set_iq(ctx: commands.Context, member: discord.Member, new_iq: int):
            with Data.RW('iq_scores.json') as iqs:
                iqs[str(member.id)] = new_iq

            await self.command_success(ctx.message)



        @self.command(help='Server add text channel')
        @commands.is_owner()
        async def sat(ctx, channel:discord.TextChannel, cname:str):
            client.server.add_text_channel(channel, cname)
            
            await client.command_success(ctx.message)


        @self.command(help='Enable text channels')
        @commands.is_owner()
        async def enable(ctx, *channels):
            channels = self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).enable())
            else:
                await ctx.send('\n'.join(reply))


        @self.command(help='Disable text channels')
        @commands.is_owner()
        async def disable(ctx, *channels):
            channels = self.get_channels_from_tuple(*channels)
            reply = []
            for channel in channels:
                reply.append(MyChannel(channel).disable())
            else:
                await ctx.send('\n'.join(reply))


        @self.command(help='List disabled channels')
        @commands.is_owner()
        async def listd(ctx):
            reply = []
            with Data.R('config') as config:
                for ch_id in config['disabled_channels']:
                    reply.append(client.get_channel(ch_id).mention)

            return await ctx.send(
                embed=discord.Embed(
                    title='Disabled Text Channels:',
                    description='\n'.join(reply),
                    colour=Color.from_rgb(255, 0, 0)
                )
            )


        @self.command(help='Restart the bot')
        @commands.is_owner()
        async def reboot(ctx, *args):
            arguments = {'update': self.update_bot, 'clear': self.clear_sceen}

            for arg in args:
                try:
                    await arguments[arg](ctx)
                except KeyError as e:
                    raise BadArgument("Argument %s not found." % e)
            
            print('Rebooting...')
            await ctx.send("Rebooting...")
            
            with open('reboot_id', 'w') as f:
                f.write(str(ctx.channel.id))

            await client._exit()


        @self.command(help='Removes warns')
        @commands.is_owner()
        async def del_warn(ctx, id):
            warnings = Data.read('warnings.json')

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
                Data('warnings.json').dump(warnings)

                await self.client.command_success(ctx.message)


        @self.command(help='Send embed msg')
        @commands.is_owner()
        async def embed(ctx, channel:discord.TextChannel, *, title_msg): # Here i test my embed messages 
            title, msg = title_msg.split('\\')
            await channel.send(
                embed=discord.Embed(
                    title=title, 
                    description=msg, 
                    colour=discord.Color.blue()
                )
            )


        @self.command()
        @commands.is_owner()
        async def embed_edit(ctx: commands.Context, channel:discord.TextChannel, id:int, *, content:str):
            msg = await channel.fetch_message(id)

            msg_embed = msg.embeds[0]

            embed = discord.Embed(title=msg_embed.title, description=content, colour=msg_embed.colour)

            await msg.edit(embed=embed)

            await self.command_success(ctx.message)


        @self.command(help='DM user as bot')
        @commands.is_owner()
        async def dm(ctx, argument : Union[discord.Member, discord.TextChannel, str], *, args : Union[discord.Member, str]=None):
            def to_(member:discord.Member) -> discord.Embed:
                return discord.Embed().set_author(name=member, icon_url=member.avatar_url)

            
            if isinstance(argument, (discord.member.Member, discord.channel.TextChannel)):
                if args is None: return await ctx.send("You can't send empty message.")

                await self.human_like_send(argument, args)
                if type(argument) is discord.member.Member:
                    await ctx.message.reply(embed=to_(member=argument))
            elif isinstance(argument, str):
                if argument in ['hist', 'history']:
                    if isinstance(args, discord.member.Member):
                        limit = 10
                        member = args
                    else:
                        _args = args.split(' ')
                        member = discord.utils.get((ctx.guild).members, id=int(_args[0]))
                        limit = int(_args[1])

                    await self.get_history(ctx, member, limit)
                elif argument in ['del', 'delete']:
                    try:
                        rmsg = await self.reference(ctx.message)
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
                            await self.command_success(ctx.message)
                elif argument in ['view', '-d']:
                    try:
                        rmsg = await self.reference(ctx.message)
                    except Reference.NoneReference as e:
                        await ctx.send(e)
                    else:
                        embed = rmsg.embeds[0].to_dict()
                        member_id = int(embed['footer']['text'])
                        member = client.get_user(member_id)
                        message_id = int(args or embed['description'].split(' ')[-1]) 
                        await self.view_message(ctx, member, message_id)
                else:
                    try:
                        rmsg = await self.reference(ctx.message)
                    except Reference.NoneReference as e:
                        return await ctx.send(e)
                    else:
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

                        await self.command_success(ctx.message)
            else:
                print('huh?')
                print(type(argument))


        @self.command()
        @commands.is_owner()
        async def cleardm(ctx, amount=50): # This will delete this bot message's
            messages = await ctx.history(limit=amount).flatten()
            for msg in messages:
                if msg.author == client.user:
                    await msg.delete()


        @self.command(help='Spam user')
        @commands.is_owner()
        async def spam(ctx, spam_to : Union[discord.Member, discord.TextChannel], *, message: str):
            try:
                loop = int(message.split(' ')[-1])
            except ValueError:
                loop = 1
            finally:
                if isinstance(spam_to, discord.Member) and spam_to.bot:
                    return await ctx.send("Can't spam bot.")

                message = message[:-1]

                for _ in range(loop):
                    await spam_to.send(message)
                else:
                    await ctx.reply("Done spamming **%s**." % spam_to)
            
            


        @self.command(help='New reaction roles')
        @commands.is_owner()
        async def newrr(ctx, *, args:str):
            #roles_channel = self.server_get_channel(cname='r')

            try:
                message = await self.reference(ctx.message)
            except Reference.NoneReference as e:
                return await ctx.send(e)
            else:            
                blocks = Data.read('reactions.json')
                blocks[str(message.id)] = {}
                
                for block in args.split(' / '):
                    emoji_and_role = block.split(' ')
                    blocks[str(message.id)][emoji_and_role[0]] = int(emoji_and_role[1][3:-1])
                    
                    self.client.reactions_command[message.id] = self.client.on_role_react_add
                    self.client.reactions_command_remove[message.id] = self.client.on_role_react_remove

                    await message.add_reaction(emoji_and_role[0])
                else:
                    Data('reactions.json').dump(blocks)

                await ctx.message.delete()


        @self.command(help='List all roles | members')
        @commands.is_owner()
        async def listall(ctx, members_or_role:str):
            if members_or_role.lower() == 'roles':
                the_list = [role for role in ctx.guild.roles if not str(role) == '@everyone']
            elif members_or_role.lower() == 'members':
                the_list = ctx.guild.members 
            else:
                return await ctx.send("List all WHAT?")

            await ctx.send(embed=discord.Embed(title='%i total:' % len(the_list), description='\n'.join([thing.mention for thing in the_list])))


        @self.command(help='Do not raise')
        @commands.is_owner()
        async def dnr(ctx):
            try:
                # My own class that returns the replied message.
                rmsg = await self.reference(ctx.message)
            except Reference.NoneReference as e: 
                # If the user didn't reply to a message
                return await ctx.message.reply(e)
            else:
                # If the user has replied to a message
                embed_footer = str(rmsg.embeds[0].to_dict()['footer']['text'])
                
                if embed_footer.startswith('<class') and embed_footer.endswith('>'):
                    error_data = Data.read('errors.json')

                    if embed_footer in error_data['do_not_raise']:
                        return await ctx.send("It's already 'dnr'")

                    error_data['do_not_raise'].append(embed_footer)

                    Data('errors.json').dump(error_data)

                    await self.command_success(ctx.message)
                else:
                    await ctx.send("'%s' does not look like an type." % embed_footer)


        @client.group(help='Edit ids.json')
        @commands.is_owner()
        async def config(ctx: commands.Context):
            if ctx.subcommand_passed is None:
                return


        @config.command(name='print')
        @commands.is_owner()
        async def _print(ctx: commands.Context, what:str):
            with Data.R('ids.json') as config:
                if what in config:
                    await ctx.send('```%s```' % '\n'.join(['%s = %s' % (name, value) for name, value in config[what].items()]))
                else:
                    await ctx.send("'%s' not found." % what)
                

        
        @config.command()
        @commands.is_owner()
        async def channels(ctx: commands.Context, name:str, value: Union[discord.TextChannel, int]):
            with Data.RW('ids.json') as config:
                if name in config['channels']:
                    if isinstance(value, discord.TextChannel):
                        value = value.id

                    config['channels'][name] = value
                    await self.command_success(ctx.message)
                else:
                    await ctx.send("'%s' not found." % name)


        @config.command()
        @commands.is_owner()
        async def msgs(ctx: commands.Context, name:str, value: int):
            with Data.RW('ids.json') as config:
                if name in config['msgs']:
                    config['msgs'][name] = value
                    await self.command_success(ctx.message)
                else:
                    await ctx.send("'%s' not found." % name)


        @config.command()
        @commands.is_owner()
        async def roles(ctx: commands.Context, name:str, value:Union[discord.Role, int]):
            with Data.RW('ids.json') as config:
                if isinstance(value, discord.Role):
                    value = value.id

                if name in config['roles']:
                    config['roles'][name] = value
                    await self.command_success(ctx.message)
                else:
                    await ctx.send("'%s' not found." % name)


        @self.command(help='Remove member exp')
        @commands.is_owner()
        async def remove_exp(ctx: commands.Context, member: discord.Member, exp:int):
            member_level = await Leveling_System.remove_exp(client, member, exp)


        @self.command(help='Add exp to member')
        @commands.is_owner()
        async def add_exp(ctx: commands.Context, member: discord.Member, exp:int):
            member_level = await Leveling_System.add_exp(client, member, exp)


        @self.command(help='Add role to shop.json')
        @commands.is_owner()
        async def add_role(ctx: commands.Context, role: discord.Role, price:int, *, description:str):
            with Data.RW('shop.json') as shop:
                shop[str(role.id)] = {}
                shop[str(role.id)]['price'] = price
                shop[str(role.id)]['description'] = description

                buy_role_msg = []

                for name, value in shop.items():
                    buy_role_msg.append(f"<@&{name}> - {value['description']}\nPrice: $**{value['price']}**\nTo buy this role: `{client.prefix}buy role {name}`")

            buy_role_msg = '\n\n'.join(buy_role_msg)

            await client.buy_role_msg.edit(content=buy_role_msg)

            await self.command_success(ctx.message)


        @self.command(help='Add TODOs')
        @commands.is_owner()
        async def todo(ctx: commands.Context, *, TODO:str=None):
            with Data.RW('todo.json') as todos:
                todos_list = todos['todos']

                if TODO is None:
                    todos_show = []

                    for idx, todo in enumerate(todos_list):
                        todos_show.append('%i: %s' % (idx, todo))

                    return await ctx.send('\n'.join(todos_show) if len(todos_show) != 0 else "Nothing.")
                elif TODO.split(' ')[0] in ['del', 'delete']:
                    try:
                        idx = int(TODO.split(' ')[1])

                        todos['todos'].pop(idx)
                    except IndexError as e:
                        return await ctx.send(e)
                    except ValueError as e:
                        return await ctx.send(e)
                    else:
                        return await self.command_success(ctx.message)
                else:
                    todos['todos'].append(TODO)

                    await self.command_success(ctx.message)


        @self.command(help='Do IQ test')
        @commands.is_owner()
        async def iqtest(ctx: commands.Context, member: discord.Member=None):
            member = member or ctx.author

            iq = self.client.get_iq(member, see_only=False)

            embed = discord.Embed(description='IQ: **%i**' % iq, colour=Color.blue())
            embed.set_author(name=member, icon_url=member.avatar_url)

            await ctx.send(embed=embed)


        @self.command()
        @commands.is_owner()
        async def price_for_iq(ctx: commands.Context, new_price_for_iq: int) -> None:
            with Data.RW('config.json') as config:
                config['price_for_iq'] = new_price_for_iq


    """
    Commands functions:
    """

    # reboot command
    async def update_bot(self, ctx):
        await ctx.send("**Updating...**")
        _code = os.system('echo $(git pull) > update.txt')
        with open('update.txt') as f:
            update_status = f.read()
        
        await ctx.send(embed=discord.Embed(title='Update status:', description='```\n%s```' % update_status).set_footer(text='exit_code: %s' % _code))
        
        with open('update.txt', 'w') as f:
            pass

    
    # reboot command
    async def clear_sceen(self, ctx):
        os.system('clear')


    # enable disable commands
    def get_channels_from_tuple(self, *channels):
        _channels = []
        for channel in channels:
            if channel.startswith('<#') and channel.endswith('>'):
                _channels.append(self.client.get_channel(int(channel[2:-1])))
            else:
                raise ChannelNotFound("%s is not a channel." % channel)
        else:
            return _channels


    # dm command
    async def human_like_send(self, member:Union[discord.member.Member, discord.channel.TextChannel], message:str):
        if not message.startswith('https://'):
            async with member.typing():
                await asyncio.sleep(len(message) / 10)

        await member.send(message)


    # dm command
    async def get_history(self, ctx, member:discord.Member, limit:int):
        member_dm_history_msg = await member.history(limit=limit).flatten()

        embed = discord.Embed(title='DM history:')
        embed.set_footer(text=str(member.id))
        embed.set_author(name=member, icon_url=member.avatar_url)

        for message in member_dm_history_msg[::-1]:
            content = await self.client.commet_lines(message.content)
            embeds = message.embeds

            value = '%s%s' % (content, '' if len(embeds) == 0 else '\n`%s`' % str(embeds))

            embed.add_field(name=message.author, value='%s\n﹂ %i' % (value, message.id), inline=False)
        else:
            await ctx.send(embed=embed)
    


    async def view_message(self, ctx, member:discord.Member, message_id:int):
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


class Admin_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(help="Pin message")
        @self.is_admin()
        async def pin(ctx):
            try:
                rmsg = await self.reference(ctx.message)
            except Reference.NoneReference as e:
                return await ctx.send(e)
            else:
                await rmsg.pin()
    

        @self.command(help='Clear text channel')
        @self.is_admin()
        async def clear(ctx, amount:int=0):
            await ctx.channel.purge(limit=amount + 1)


        @self.command(help='Kick member')
        @self.is_admin()
        async def kick(ctx, member : discord.Member, *, reason=None):
            await member.kick(reason=reason)
            await ctx.message.add_reaction('🦶🏽')
            await ctx.send(f'**{member}** kicked!')


        @self.command(help='Ban member')
        @self.is_admin()
        async def ban(ctx, member : discord.Member, *, reason=None):
            bans_says = ['**{}** is banned from this server.', 'Yes! That poes **{}** is banned from this server!']
            
            embed = discord.Embed(title='!! YOU GOT BANNED !!', colour=Color.from_rgb(255, 0, 0))
            embed.description = 'Reason: **%s**' % reason
            embed.set_footer(text='%s - Owner: %s' % (ctx.guild.name, ctx.guild.owner))

            await member.send(embed=embed)
            
            await member.ban(reason=reason)
            await ctx.message.add_reaction('✅')
            await ctx.send(random.choice(bans_says).format(member))


        @self.command(help='List banned members')
        @commands.has_role(client.staff_role_id)
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


        @self.command(help='Unban member')
        @self.is_admin()
        async def unban(ctx, id:int):
            user = await client.fetch_user(id)
            await ctx.guild.unban(user)
            await self.client.command_success(ctx.message)


        @self.command(help='Warn member')
        @commands.has_role(client.staff_role_id)
        async def warn(ctx, user : discord.Member, *, reason=None):
            if user.id == ctx.guild.owner.id:
                await ctx.send("Fuck you! %s" % ctx.author.mention)
                return 
            
            warnings = Data.read('warnings.json')
            
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

                Data('warnings.json').dump(warnings)


        @self.command(aliases=['warns', 'warns_id'], help='List members warns')
        @commands.has_role(client.staff_role_id)
        async def warnings(ctx, member : discord.Member=None):
            warnings = Data.read('warnings.json')
            
            embed = discord.Embed(
                title="Warning List",
                color=discord.Color.red()
            )
            if member is None:
                for user_id in warnings:
                    user = client.get_user(int(user_id))
                    if ctx.message.content.startswith('%swarns_id' % (self.client.prefix)): user = '%s (%i)' % (user.name, user.id)
                    user_reasons = []
                    for msg_id in warnings[user_id]:
                        if ctx.message.content.startswith('%swarns_id' % (self.client.prefix)):
                            user_reasons.append('• `%s` ~ (%s)' % (str(warnings[user_id][msg_id]), msg_id))    
                        else:
                            user_reasons.append('• `%s`' % (str(warnings[user_id][msg_id])))
                    user_reasons = '\n'.join(user_reasons)
                    embed.add_field(name='%s, reason(s):' % user, value=user_reasons, inline=False)
            else:
                user_reasons = []
                for msg_id in warnings[str(member.id)]:
                    if ctx.message.content.startswith('%swarns_id' % (self.client.prefix)):
                        user_reasons.append('• `%s` ~ (%s)' % (str(warnings[str(member.id)][msg_id]), msg_id))    
                    else:
                        user_reasons.append('• `%s`' % (str(warnings[str(member.id)][msg_id])))
                user_reasons = '\n'.join(user_reasons)
                if ctx.message.content.startswith('%swarns_id' % (self.client.prefix)): member = '%s (%i)' % (member.name, member.id)
                embed.add_field(name='%s, reason(s):' % member, value=user_reasons, inline=False)

            await ctx.send(embed=embed)


        @self.command(help='Announce a messsage')
        @self.is_admin()
        async def announce(ctx, *, args=None):
            try:
                replied_message = await self.reference(ctx.message)
            except Reference.NoneReference as e:
                await ctx.message.reply(e)
            else:
                embed = discord.Embed(description=replied_message.content)
                embed.set_author(name=replied_message.author, icon_url=replied_message.author.avatar_url)

                server_announcement_channel = self.client.server.get_channel(cname='sa')   

                await server_announcement_channel.send('@everyone' if args == 'everyone' else args, embed=embed)

                await self.client.command_success(ctx.message)


        @self.command(help='View json')
        @self.is_admin()
        async def view_json(ctx, file_name):
            if file_name.endswith('.json'):
                with open('%s%s' % (Data.data_folder, file_name)) as f:
                    try:
                        await ctx.send("```json\n%s\n```" % (f.read()))
                    except Exception:
                        await ctx.send(file=discord.File('%s%s' % (Data.data_folder, file_name)))
            else:
                raise Exception("**%s does not end with '.json'**" % (file_name))


        @self.command(help='List all json files')
        @self.is_admin()
        async def list_json(ctx):
            json_files = []
            for f in os.scandir(Data.data_folder):
                if f.name.endswith('.json'):
                    json_files.append(f.name)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title='All json files:',
                        description='```%s```' % '\n'.join(json_files)
                    )
                )


        @self.command(help='List all python files')
        @self.is_admin()
        async def list_scripts(ctx):
            py_files = [py_file.name for py_file in os.scandir('scripts/') if py_file.name.endswith('.py')]
            
            for idx, file in enumerate(py_files):
                lines = 0
                with open('scripts/' + file) as f:
                    for line in f.readlines():
                        lines += 1
                py_files[idx] = '`%s` : **%i** lines' % (file, lines)

            embed = discord.Embed(
                title="All the script files:",
                description='\n'.join(py_files)
            )
            await ctx.send(embed=embed)


        @self.command(help='Tic-tac-toe winner says')
        @commands.has_role(client.staff_role_id)
        async def ttt_winners_says(ctx: commands.Context, *, say:str=None):
            with Data.RW('server.json') as f:
                if say is None:
                    await ctx.send('\n'.join(f['ttt_winners_says']))
                else:
                    f['ttt_winners_says'].append(say)
            await self.command_success(ctx.message)

    """
    Command functions:
    """


    def is_admin(self):
        def wrapper(ctx):
            return ctx.author.guild_permissions.administrator
        return commands.check(wrapper)
            

    def command(self, *args, **kwargs):
        return super().command(*args, category='ADMIN', **kwargs)



class Nsfw_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='NSFW', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(help='r/boobs')
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def boobs(ctx, limit:int=1):
            await self.client.reddit(ctx, 'boobs', limit)


        @self.command(help='r/ass')
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def ass(ctx, limit:int=1):
            await self.client.reddit(ctx, 'ass', limit)


        @self.command(help='r/hentai')
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def hentai(ctx: commands.Context, limit:int=1):
            await self.client.reddit(ctx, 'hentai', limit)


        @self.command(help='r/porn')
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def porn(ctx: commands.Context, limit:int=1):
            await self.client.reddit(ctx, 'porn', limit)


        @self.command(help='r/rule34')
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def rule34(ctx: commands.Context, limit:int=1):
            await self.client.reddit(ctx, 'rule34', limit)


        @self.command(help="THE BEST ;)")
        @commands.is_nsfw()
        @commands.has_role(self.client.nsfw_pp_role_id)
        async def traps(ctx: commands.Context, limit:int=1):
            await self.client.reddit(ctx, 'traps', limit)


class Reddit_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='REDDIT', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(name='r/', help='Get post from reddit.')
        @commands.has_role(client.reddit_role_id)
        async def r(ctx, subreddit:str, limit:int=1):
            await self.client.reddit(ctx, subreddit, limit)


        @self.command(help='Awww so cute!')
        @commands.has_role(client.reddit_role_id)
        async def awww(ctx, limit:int=1):
            await self.client.reddit(ctx, 'awww', limit)


        @self.command(help='Yummy!')
        @commands.has_role(client.reddit_role_id)
        async def food(ctx, limit:int=1):
            await self.client.reddit(ctx, 'foodporn', limit)


        @self.command(help='r/memes')
        @commands.has_role(client.reddit_role_id)
        async def memes(ctx, limit:int=1):
            await self.client.reddit(ctx, 'memes', limit)


        @self.command(help='r/dankmemes')
        @commands.has_role(client.reddit_role_id)
        async def dankmemes(ctx, limit:int=1):
            await self.client.reddit(ctx, 'dankmemes', limit)


        @self.command(help='Anime grill')
        @commands.has_role(client.anime_role_id)
        async def animegirl(ctx, limit:int=1):
            await self.client.reddit(ctx, 'cuteanimegirls', limit)



class Fun_Commands(Bot_Commands):
    def command(self, *args, **kwargs):
        return super().command(*args, category='FUN', **kwargs)

    def __init__(self, client) -> None:
        super().__init__(client)


        @self.command(aliases=['ttt'], help='Tic-tac-toe game')
        async def tictactoe(ctx, player1: Union[discord.Member, str], player2 : discord.Member=None):
            if isinstance(player1, str):
                if player1 == 'bvb':
                    player1 = discord.utils.get(ctx.guild.members, id=816668604669755433) # This ID is local bot
                    player2 = discord.utils.get(ctx.guild.members, id=815991197369630730) # This ID is Hey Sexy Bot
            else:
                if player2 is None:
                    player2 = ctx.author

            if not isinstance(player1, discord.Member): 
                raise discord.ext.commands.MemberNotFound("**{}**".format(player1))
            
            if player1 == player2:
                raise discord.ext.commands.BadArgument("Player 1 and Player 2, can't be the same.")
            
            ttt_game = TicTacToe(player1, player2, ctx, self.client.ttt_running, client)
            self.client.ttt_running.append(ttt_game)
            ttt_game.all_running_ttt = self.client.ttt_running
            ttt_game.current_game = ttt_game
            game_msg = await ctx.send(await ttt_game.print())
            ttt_game.game_msg = game_msg

            client.reactions_command[game_msg.id] = self.on_ttt_reaction
            
            if (player1.bot == False and player2.bot == False) or (not player1.bot or not player2.bot):
                for emoji in ttt_game.reactions:
                    asyncio.create_task(game_msg.add_reaction(emoji=emoji))
            
            #embed = discord.Embed(description=f"**{ttt_game.turn.name}** turn")
            embed = discord.Embed(colour=ttt_game.turn_colour[ttt_game.turn.id]).set_author(name='%s - turn' % ttt_game.turn.name, icon_url=ttt_game.turn.avatar_url)

            ttt_game.whos_turn_msg = await ctx.send(embed=embed)
            
            if ttt_game.turn.bot:
                await asyncio.sleep(2.0)
                await ttt_game.move(await ttt_game.smart_bot_move())
            
            if not player1.bot or not player2.bot: # This checks if a user didn't make a move for a while
                make_move_msgs = ttt_game.make_move_msgs
                wait_time = 40
                while ttt_game.running:
                    count = ttt_game.count
                    await asyncio.sleep(wait_time)
                    if count == ttt_game.count:
                        make_move_msg = await ttt_game.game_msg.reply(f'{ttt_game.turn.mention} make a move!')
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


        @self.command(help="Get IQ")
        async def iq(ctx, member:discord.Member=None):
            member = member or ctx.author
            
            iq = self.client.get_iq(member, see_only=True)

            embed = discord.Embed(description='IQ: **%i**' % iq, colour=Color.blue())
            embed.set_author(name=member, icon_url=member.avatar_url)

            await ctx.send(embed=embed)


        @self.command(help="Gay test", aliases=['gay'])
        async def gaytest(ctx, member:discord.Member=None):
            member = member or ctx.author

            say = self.client.get_gay_test()

            embed = discord.Embed(description=say, colour=Color.from_rgb(255,105,180))
            embed.set_author(name=member, icon_url=member.avatar_url)

            await ctx.send(embed=embed)


        @self.command(aliases=['g'], help='Guess between 0-6')
        async def guess(ctx, user_guess:int):
            if user_guess >= 0 and user_guess <= 6:
                bot_guess = random.randint(0, 6)
                
                embed = discord.Embed(description="I guess: **%i**\nYou guessed: **%i**"  % (bot_guess, user_guess), colour=Color.blue())
                await ctx.send(embed=embed)
                if user_guess == bot_guess:
                    exp = random.choice([600, 1000, 500, 400, 1200, 4000, 10, 1, 69, 666, 777, 999])
                    
                    member_levels = Leveling_System(str(ctx.author.id), exp)
                    member_levels.add()

                    await ctx.send("Wow! + **%i** exp" % exp)
            else:
                await ctx.send("You must guess between 0-6")


        @self.command(aliases=['pp'], help='PP size')
        async def ppsize(ctx: commands.Context, member:discord.Member=None):
            member = member or ctx.author
            member_roles = [role.id for role in member.roles]

            embed = discord.Embed(colour=Color.purple())
            embed.set_author(name=member, icon_url=member.avatar_url)
            
            if client.female_role_id in member_roles: # Checks if that member has a female role
                pp = "**Females don't have PP!**"
            elif client.male_role_id in member_roles or client.transgender_role_id in member_roles: # checks if that member has male or transgender role
                try:
                    member_iq = Data.read('iq_scores.json')[str(member.id)]
                except KeyError as e:
                    member_iq = random.randint(0, 10)

                pp_size = int(member_iq / (10 if member_iq > 50 else 1.5))

                pp = ('8%sD' % ('=' * pp_size)) if pp_size != 0 else None

                embed.title = "PP size:"
                embed.set_footer(text="%icm" % pp_size)
            else:
                pp = "**I don't know what gender you are.**"

            embed.description = pp

            await ctx.send(embed=embed)


        @self.command(name='8ball', help='Ask the magic')
        async def _8ball(ctx: commands.Context, question:str):
            embed = discord.Embed(
                title=random.choice(self.client._8ball_says), 
                colour=Color.from_rgb(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
            )

            await ctx.reply(embed=embed)


    """
    Command functions
    """

    # tic-tac-toe command
    async def on_ttt_reaction(self, payload:discord.RawReactionActionEvent):
        ttt_running = self.client.ttt_running
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
                                    try:
                                        del self.client.reactions_command[ttt_game.whos_turn_msg.id]
                                    except KeyError as e:
                                        print("Can't delete: %s" % e)
                                    ttt_running.remove(ttt_game)
                                    await self.client.all_commands['tictactoe']._callback(ctx=ttt_game.ctx, player1=ttt_game.player_1, player2=ttt_game.player_2)
                                    ttt_game.destroy = False
            except NameError:
                pass





class Nc_Commands(Bot_Commands):
    def __init__(self, client) -> None:
        super().__init__(client)
        
        """
        No category commands:
        """
        @self.command(help=".help [command_name]", des="To help you with the other commands.")
        async def help(ctx, command:str=None):
            member = ctx.author
            categories = client.categories.copy()

            categories = self.help_category_check(ctx, member, categories)

            embed = discord.Embed(colour=Color.purple())

            if command is None:
                embed.title = 'All categories:'
                embed = self.help_get_categories(embed, categories)
                embed.set_footer(text='%shelp <category_name>' % client.prefix)
            elif command.lower() == 'all':
                embed.title = "All commands:"
                embed = self.help_get_all_commands(embed, categories)
                embed.set_footer(text='%shelp <command_name>' % client.prefix)
            else:
                if command.upper() in categories:
                    embed = self.help_get_all_commands(embed, {command.upper(): categories[command.upper()]})
                else:
                    found = False
                    for category_name, commands in categories.items():
                        if command in commands:
                            found = True
                            embed.add_field(
                                name=category_name,
                                value='```%s%s %s```%s' % (
                                    await client.get_prefix(ctx.message), 
                                    command, 
                                    commands[command]['args'],
                                    commands[command]['help']
                                ), 
                                inline=False
                            )
                            break
                    else:
                        if not found:
                            return await ctx.message.reply(
                                embed=discord.Embed(
                                    description="""Command "**%s**" not found.""" % command
                                ).set_footer(
                                    text='%shelp <command_name>' % client.prefix
                                )
                            )


            await ctx.send(embed=embed)


        @self.command(help="Bot's latency")
        async def ping(ctx):
            return await ctx.message.reply(
                embed=discord.Embed(
                    description="**%i**ms" % round(client.latency * 1000),
                    colour=Color.blue()
                )
            )


        @self.command(help='Member info')
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


        @self.command()
        async def server(ctx: commands.Context):
            server = ctx.guild

            embed = discord.Embed(description='**%s**' % server.description, colour=Color.from_rgb(255,105,180))
            embed.set_author(name=server, icon_url=server.icon_url)
            embed.set_thumbnail(url=server.icon_url)

            embed.add_field(name='ID:', value='`%i`' % server.id)
            embed.add_field(name='Owner:', value='`%s`' % server.owner, inline=False)
            embed.add_field(name='Member count:', value='`%i`' % server.member_count)
            embed.add_field(name='Role count:', value='`%i`' % len(server.roles))
            embed.add_field(name='Bans:', value='`%i`' % len(await server.bans()))
            embed.add_field(name='Region:', value='%s`' % ':flag_za: `South Africa' if str(server.region) == 'southafrica' else server.region, inline=False)
            embed.add_field(name='Rules channel:', value=server.rules_channel.mention, inline=False)
            embed.add_field(name='AFK channel:', value=server.afk_channel.mention)
            embed.set_footer(text='Created at: %s' % server.created_at.date())
            
            await ctx.send(embed=embed)


        @self.command(help='Profile pic', aliases=['av'])
        async def pfp(ctx: commands.Context, member : discord.Member=None):
            member = member or ctx.author
            _pfp = member.avatar_url

            embed = discord.Embed(colour=Color.blue())
            embed.set_author(name=member.display_name + '  -  profile pic:', icon_url=_pfp)
            embed.set_image(url=_pfp)

            msg = await ctx.send(embed=embed)
        
            opinion = random.choice(self.client.pfp_says)

            if opinion is not None:
                await msg.reply(opinion)



        @self.command(help='Total lines of code')
        async def lines(ctx):
            lines = 0

            for file in os.scandir('scripts/'):
                if file.name.endswith('.py'):
                    with open('scripts/' + file.name) as f:
                        lines += len(f.readlines())

            await ctx.send(
                embed=discord.Embed(
                    description='I have **%i** lines of code.' % (lines),
                    colour=Color.blue()
                )
            )


        @self.command(help='Get member ID')
        async def id(ctx, member : discord.Member=None):
            member = member or ctx.author

            await ctx.message.reply('**%i**' % (member.id))


        @self.command(help='Get member from ID')
        async def who(ctx, user_id : int):
            await ctx.message.reply('**%s**' % (client.get_user(user_id)))


        @self.command(help="Member status")
        async def status(ctx: commands.Context, member: Union[discord.Member, str]=None, args=None):
            if isinstance(member, str):
                args = member
                member = ctx.author
            
            def get_nice_type(_type):
                return str(_type[0][0].upper() + _type[0][1:])


            status_icon = {
                'online': 'https://emoji.gg/assets/emoji/9166_online.png',
                'dnd': 'https://emoji.gg/assets/emoji/7907_DND.png',
                'offline': 'https://emoji.gg/assets/emoji/7445_status_offline.png',
                'idle': 'https://i.redd.it/kp69do60js151.png'
            }

            member = member or ctx.author
            _status = member.status

            status_platform = member._client_status.copy()

            del status_platform[None]

            if str(_status) == 'dnd':
                _status = 'Do Not Disturb'

            _status = '%s  -  %s' % (_status, ', '.join(list(status_platform)))

            activities = member.activities

            embed = discord.Embed(colour=Color.blue())
            embed.set_author(name=member, icon_url=member.avatar_url)
            embed.set_footer(text=_status, icon_url=status_icon[str(member.status)])

            if args == 'more':
                status = []

                for act in activities:
                    # TODO: Clean up code

                    if str(type(act)) == "<class 'discord.activity.Activity'>":
                        details = ''
                        if act.details is not None:
                            details = '\n> %s\n> %s\n%s' % (act.details, act.state, act.url or '')

                        status.append("%s **%s**%s" % (get_nice_type(act.type), act.name, details))
                    elif str(type(act)) == "<class 'discord.activity.Spotify'>": # The user is playing spotify
                        embed.set_thumbnail(url=act.album_cover_url)
                        status.append("%s\n> **%s** - by __%s__\n> on __%s__" % ('%s To %s' % (get_nice_type(act.type), act), act.title, ', '.join(act.artists), act.album))
                    else:
                        status.append('%s **%s**' % (get_nice_type(act.type), act))

                status = '\n'.join(status)

                embed.description = status
            elif args == '-d':
                embed.description = str(activities)
                embed.set_footer(text=str(member._client_status))
            else:
                if not len(activities) == 0:
                    _type = get_nice_type(activities[0].type)
                    _game = activities[0].name

                    if not _type == "Playing":
                        if not activities[0].emoji is None:
                            _game = "%s %s" % (activities[0].emoji, _game)

                    embed.description="%s **%s**" % (_type, _game)

            await ctx.send(embed=embed)


        @self.command(help="List member's IQ")
        async def iqlist(ctx):
            with Data.RW('iq_scores.json') as iqscores:
                iqscores_copy = iqscores.copy()

                users = []

                for user_id in iqscores_copy:
                    try:
                        users.append('%s IQ score: **%i**' % (client.get_user(int(user_id)).mention, iqscores[user_id]))
                    except AttributeError:
                        del iqscores[user_id]

            embed = discord.Embed(
                title='%s members IQ:' % ctx.guild,
                description='\n'.join(users)
            )
            await ctx.send(embed=embed)


        @self.command(help="Last deleted message")
        async def snipe(ctx):
            if ctx.channel.id in self.client.last_deleted_message:
                embed = discord.Embed(
                    description="Last deleted message in %s from %s @ **%s**:" % (ctx.channel.mention, 
                    client.get_user(self.client.last_deleted_message[ctx.channel.id]['user']).mention,
                    self.client.last_deleted_message[ctx.channel.id]['time']
                    ),
                    colour=Color.from_rgb(255, 0, 0)
                )
                embed.add_field(name='Message:', value=self.client.last_deleted_message[ctx.channel.id]['content'], inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("There's no recently deleted message in %s" % (ctx.channel.mention))


        @self.command(help='List tic-tac-toe games')
        async def list_ttt(ctx):
            des = str()
            for ttt in self.client.ttt_running:
                des = '%s\n%s' % (des, ttt)
            embed = discord.Embed(
                title='All running tic-tac-toe games:', 
                description=des
            )
            await ctx.send(embed=embed)


        @self.command(help="Bot's uptime")
        async def uptime(ctx): #TODO: cleanup code
            current_time = datetime.now()
            cal_uptime = current_time - self.client.on_ready_time
            
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
                embed = discord.Embed(colour=Color.blue())
                embed.set_author(name=client.user, icon_url=client.user.avatar_url)
                embed.add_field(name='Uptime:', value=cal_uptime)
                await ctx.send(embed=embed)


        @self.command(help='Forward message to someone')
        async def forward(ctx, *members):
            if members == ():
                members = [str(ctx.author.id)]

            try:
                rmsg = await self.reference(ctx.message)
            except Reference.NoneReference as e:
                return await ctx.message.reply(e)
            else:
                link = rmsg.jump_url
                
                embed = discord.Embed(description=rmsg.content)
                embed.set_footer(text='Forwarded')
                embed.set_author(name='Message link', url=link, icon_url=rmsg.author.avatar_url)

                for member in members:
                    await self.get_member(member).send('From **%s**' % ctx.author, embed=embed)
                else:
                    await self.command_success(ctx.message)


        @self.command(help="View command source code")
        async def code(ctx, *, command_name:str):
            try:
                command = client.all_commands[command_name]._callback
            except KeyError:
                raise discord.ext.commands.errors.CommandNotFound("Command **%s** not found." % command_name)
            else:
                _source_code = inspect.getsource(command)

                source_file = 'source_code.py'
                with open(source_file, 'w') as f:
                    f.write(_source_code)
                
                file = discord.File(source_file)
                
                await ctx.send(embed=discord.Embed(description='**%s** source code:' % command_name, colour=discord.Colour.green()), file=file)

                with open(source_file, 'w') as f:
                    f.write('')


        @self.command()
        async def google(ctx, *, google_search:str):
            _5_searchs = [link for link in search(google_search, stop=5, pause=0.1)]

            await ctx.send(random.choice(_5_searchs))



        @client.group(help='Buy stuff')
        async def buy(ctx: commands.Context):
            if ctx.channel.id == client.shop_channel.id:
                if ctx.subcommand_passed is None:
                    return await ctx.reply("What you gonna buy??")
            else:
                return await ctx.reply("You can only buy in %s" % client.shop_channel.mention)


        @buy.command(help='Buy roles')
        async def role(ctx: commands.Context, role: discord.Role):
            if ctx.channel.id == client.shop_channel.id:
                member = ctx.author

                if role in member.roles:
                    return await ctx.reply("You already have that role. lol")

                roles_to_buy = Data.read('shop.json')

                if str(role.id) in roles_to_buy:
                    try:
                        level = Leveling_System(str(member.id), 0) 
                        before_money = level.money
                        level.buy(roles_to_buy[str(role.id)]['price'])
                        after_money = level.money
                    except Exception as e:
                        return await ctx.reply(e)
                    else:
                        await member.add_roles(role)

                        await ctx.reply("You had $**%i**, now: $**%i**" % (before_money, after_money))

                        await self.command_success(ctx.message)
                else:
                    await ctx.send("Can't buy this role.")
            else:
                return await ctx.reply("You can only buy in %s" % client.shop_channel.mention)


        @buy.command(help="Increase IQ")
        async def iq(ctx: commands.Context, amount_of_iq: int) -> None:
            if not ctx.channel.id == client.shop_channel.id:
                return

            member = ctx.author
            
            member_rank = Leveling_System(str(member.id), 0)
            member_money = member_rank.money
            member_iq = self.client.get_iq(member, see_only=True)
            iq_to_add = 0

            price_for_iq = Data.read('config.json')['price_for_iq']

            if member_money >= price_for_iq:
                before_money = member_money

                while (member_money >= price_for_iq and amount_of_iq != 0):
                    iq_to_add += 1
                    member_money -= price_for_iq
                    amount_of_iq -= 1

                member_iq += iq_to_add
                
                self.client.set_iq(member, member_iq)
                member_rank.money = member_money
                member_rank.set_money()
                
                await ctx.reply(
                    embed=discord.Embed(
                        title='+ %i IQ!' % iq_to_add,
                        description="You had $**%i**, now $**%i**" % (before_money, member_money),
                        colour=Color.blue()
                    )
                )
            else:
                await ctx.send("You don't have enough money to buy **1** IQ.")



        @self.command(help='Show rank')
        async def rank(ctx: commands.Context, member: discord.Member=None):
            member = member or ctx.author

            member_levels = Leveling_System(str(member.id), 0)
            
            await ctx.send(embed=member_levels.rank_msg(member))

            return 'not_exp'


        @self.command(help='Do math')
        async def math(ctx:commands.Context, *, sum:str):
            regex = '1234567890/*-+%!.()=<> '

            for char in sum:
                if not char in regex:
                    return await ctx.send("Invalid char: **%s**" % char)
            
            def timeout(signum, frame):
                raise TimeoutError

            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(1)

            result = eval(sum)

            await ctx.send(
                embed=discord.Embed(
                    title='Math:',
                    description='%s = **%s**' % (sum, result),
                    colour=Color.blue()
                )
            )


        @self.command(aliases=['bin'], help='Binary converter')
        async def binary(ctx: commands.Context, *, text: str):
            await ctx.reply(' '.join(self.str_to_bin(text)))


        @self.command()
        async def hex(ctx: commands.Context, text: str):
            await ctx.reply(text.encode().hex())


    """
    Commands functions:
    """


    def str_to_bin(self, a_string) -> list:
        a_byte_array = bytearray(a_string, "utf8")

        byte_list = []

        for byte in a_byte_array:
            binary_representation = bin(byte)

            byte_list.append(binary_representation)

        return byte_list


    # help command
    def help_category_check(self, ctx, member:discord.Member, categories:dict) -> dict:
        """
        from help command:

        Just checks the member's permissions and deletes the categories
        """

        if not member.id == ctx.guild.owner.id:
            del categories['OWNER']
        if not member.guild_permissions.administrator:
            del categories['ADMIN'] 
        if not 'NSFW' in [role.name for role in member.roles if role.name == 'NSFW']:
            del categories['NSFW']

        return categories


    # help command
    def help_get_categories(self, embed:discord.Embed, categories:dict) -> discord.Embed:
        """
        From help command:

        if command is None:
            get_all_category
        """

        for category_name, commands in categories.items():
            embed.add_field(name=category_name, value='`%shelp %s`' % (self.client.prefix, category_name.lower()), inline=True)

        return embed


    # help command
    def help_get_all_commands(self, embed:discord.Embed, categories:dict) -> discord.Embed:
        """
        From help command:

        if command == 'all':
            help_get_all_commands
        """

        for category_name, commands in categories.items():
            embed.add_field(
                name=category_name,
                value='```{}```'.format(self.list_commands(commands)),
                inline=False
            )
        else:
            return embed


    # help command
    def left_right(self, left_text:str, right_text:str, space:int=10) -> str:
        return "• %s%s%s" % (left_text, ' ' * (space - len(left_text)), right_text)

    
    def get_biggest_num(self, numbers:list) -> int:
        biggest_num = numbers[0]

        for num in numbers:
            if num > biggest_num:
                biggest_num = num
        
        return biggest_num + 5

    #help command
    def list_commands(self, commands) -> str:
        space = self.get_biggest_num([len(str(cmd)) for cmd in commands])

        return '\n'.join([self.left_right(str(cmd), commands[cmd]['help'], space) for cmd in commands])


    def get_member(self, member:str) -> discord.Member:
        try:
            return self.client.get_user(int(member)) # Checks if member is an ID
        except ValueError:
            if member.startswith('<@!'): # Its a member
                return self.client.get_user(int(member[3:-1]))
            else:
                raise MemberNotFound('**%s**' % member)







