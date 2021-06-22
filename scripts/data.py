import json
import os
import discord



class Data:
    data_folder = 'data/'
    all_files = [file.name for file in os.scandir(data_folder)]

    def __init__(self, filename:str, write:bool=False) -> None:
        if not filename.endswith('.json'):
            filename = filename + '.json'

        self.filename = filename
        self.write = write
        self.fp = self.data_folder + self.filename

    def load(self):
        with open(self.fp) as f:
            return json.load(f)

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

    def check(*args, **kwargs):
        async def wrapper(self, func):
            config = Data.read('config')
            if not self.channel.id in config['disabled_channels']:
                return await func(*args, **kwargs)
            else:
                print("Not able to.")
        return wrapper

    @check
    async def send(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)


class Server:
    def __init__(self, guild):
        self.guild = guild
        self.id = guild.id
        self.name = guild.name
        self.owner_id = guild.owner_id
        self.text_channels = guild.text_channels
        self.get_role = guild.get_role
        self.roles = guild.roles
    

    def get_channel(self, channel_id:int=None, **kwargs):
        if channel_id is not None:
            return super().get_channel(channel_id)
        else:
            cname = kwargs.get('cname')

            if cname is None:
                raise Exception("Keyword argument 'cname' not found")

            with Data.R('server.json') as server_data:
                for channel_id, _cname in server_data['channels'].keys():
                    if cname == _cname:
                        return self.get_channel(int(channel_id))
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
        return super().get_role(role_id)



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