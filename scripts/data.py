import json
import os
import discord
import matplotlib.pyplot as plt
from datetime import datetime


class Data:
    data_folder = 'data/'
    all_files = [file.name for file in os.scandir(data_folder)]

    def __init__(self, filename:str, write:bool=False) -> None:
        if not filename.endswith('.json'):
            filename = filename + '.json'

        self.filename = filename
        self.write = write
        self.fp = self.data_folder + self.filename

    def load(self) -> json:
        with open(self.fp) as f:
            content = json.load(f)
        return content

    def dump(self, content):
        with open(self.fp, 'w') as f:
            json.dump(content, f, indent=4)

    def __enter__(self):
        self.content = self.load()
        return self.content

    def __exit__(self, *args):
        if self.write:
            with open(self.fp, 'w') as f:
                json.dump(self.content, f, indent=4)


    def clean_erros(self):
        if self.filename == 'errors.json':
            errors = self.load()

            errors['errors'] = {}

            self.dump(errors)

            print("Done cleaning errors.")
            
    
    @classmethod
    def R(cls, filename:str):
        return cls(filename)

    @classmethod
    def RW(cls, filename:str):
        return cls(filename, True)

    @classmethod
    def read(cls, filename:str) -> dict:
        return cls(filename).load()

    @classmethod
    def errors(cls, write:bool=False):
        return cls('errors.json', write)

    @classmethod
    def reddit(cls, write:bool=False):
        return cls('nsfw_subreddit.json', write)


class MyChannel:
    def __init__(self, channel:discord.TextChannel) -> None:
        self.channel = channel
        self.id = channel.id

    def enable(self):
        with Data.RW('config') as config:
            if self.id in config['disabled_channels']:
                config['disabled_channels'].remove(self.id)
                return "%s **enabled**." % self.channel.mention
            else:
                return "%s is already enabled." % self.channel.mention

    def disable(self):
        with Data.RW('config') as config:
            if self.id in config['disabled_channels']:
                return "%s already disabled." % self.channel.mention
            else:
                config['disabled_channels'].append(self.id)
                return "%s **disabled**" % self.channel.mention

    def check(func):
        async def wrapper(self, *args, **kwargs):
            config = Data.read('config')
            if not self.channel.id in config['disabled_channels']:
                return await func(self, *args, **kwargs)
            else:
                print("Not able to.")
        return wrapper

    @check
    async def send(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)


class Server:
    def __init__(self, client):
        with Data.R('server.json') as server_data:
            guild = client.get_guild(server_data['server_id'])

        self.client = client
        self.guild = guild
        self.id = guild.id
        self.name = guild.name
        self.owner_id = guild.owner_id
        self.owner = client.get_user(int(self.owner_id))
        self.text_channels = guild.text_channels
        self.get_role = guild.get_role
        self.roles = guild.roles
        self.icon_url = guild.icon_url
        self.stats_filename = 'stats.png'
    

    def get_channel(self, cname:str=None):
        if cname is None:
            raise Exception("Keyword argument 'cname' not found")

        with Data.R('server.json') as server_data:
            for channel_id, value in server_data['TC'].items():
                if cname == value['cname']:
                    return self.client.get_channel(int(channel_id))
            else:
                return None


    def add_text_channel(self, channel:discord.TextChannel, cname:str):
        with Data.RW('server.json') as server_data:
            for id, value in server_data['TC'].items():
                if cname == value['cname']:
                    raise Exception("'%s' is already in use" % cname)

            server_data['TC'][str(channel.id)] = {}
            server_data['TC'][str(channel.id)]['name'] = channel.name
            server_data['TC'][str(channel.id)]['cname'] = cname

    
    def get_role(self, role_id):
        pass


    def get_server_stats(self) -> discord.File:
        self.last_days = 7

        stats_data = Data.read('server_stats.json')

        dates, total_messgae, member_joins, member_leaves = [], [], [], []

        for stat in list(stats_data)[-self.last_days:]:
            dates.append(str(stat)[-5:])
            total_messgae.append(stats_data[stat]['total_messages'])
            member_joins.append(stats_data[stat]['member_joins'])
            member_leaves.append(stats_data[stat]['member_leaves'])

        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.suptitle("The Last %i days" % self.last_days)
        ax1.plot(dates, member_joins, label='member_joins', color='green')
        ax1.plot(dates, member_leaves, label='member_leaves', color='red')
        ax1.set_title('Member joins')
        ax1.legend()
        ax2.plot(dates, total_messgae)
        ax2.set_title('Total messages')

        fig.set_size_inches(10, 5)
        ax2.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        ax1.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        fig.savefig(self.stats_filename)

        file = discord.File(self.stats_filename)

        return file


class Reference:
    class NoneReference(Exception): 
        def __init__(self, description:str=None) -> None:
            super().__init__(description or "You didn't reply to a message.")

    def __init__(self, client) -> None:
        self.client = client


    async def __call__(self, message:discord.Message):
        self.message = message
        self.reference = message.reference

        if self.reference is None:
            raise self.NoneReference()

        return await self.get_reference()


    async def get_reference(self):
        self.channel = self.client.get_channel(self.reference.channel_id)

        message = await self.channel.fetch_message(self.reference.message_id)

        return message


    async def __aenter__(self):
        self.channel = self.client.get_channel(self.reference.channel_id)

        return await self.channel.fetch_message(self.reference.message_id)

    async def __aexit__(self, *args):
        return False


class TimeStats:
    def __init__(self):
        self.current_date = self.get_current_date()
        self.data = self.get_data()
        self.add_date()

    
    def get_current_date(self): # This will return the current date
        return datetime.now().date()


    def add_date(self): # If it's a new date then it will create the date
        if not str(self.current_date) in self.data: 
            self.data[str(self.current_date)] = {}
            self.data[str(self.current_date)]['total_messages'] = 0
            self.data[str(self.current_date)]['member_joins'] = 0
            self.data[str(self.current_date)]['member_leaves'] = 0
            self.save_data(self.data)


    def get_data(self):
        return Data.read('server_stats.json')


    def save_data(self, data):
        Data('server_stats.json').dump(data)


    def member_join(self): # This will add 1 when a member joins the server
        self.data[str(self.current_date)]['member_joins'] += 1
        self.save_data(self.data)

    
    def member_leave(self): # This will add 1 when a member leaves the serevr
        self.data[str(self.current_date)]['member_leaves'] += 1
        self.save_data(self.data)


    def on_message(self): # This will add 1 when a message been send
        self.data[str(self.current_date)]['total_messages'] += 1
        self.save_data(self.data)

    
    def cal_total_messages(self):
        total_messages = 0
        for msg in self.data:
            total_messages += self.data[msg]['total_messages']
        else:
            with open(f'{Data.data_folder}data.json') as f:
                server_data = json.load(f)
            
            server_data['total_messages'] = total_messages
            
            with open(f'{Data.data_folder}data.json', 'w') as f:
                json.dump(server_data, f, indent=2)
            
            return total_messages