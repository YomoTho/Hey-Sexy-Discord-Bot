import json
import discord


data_folder = '../data/'

class Data:
    def __init__(self, client):
        self.client = client
        self.server_data = self.get_server_data()
        self.server_id = int(self.server_data['server_id'])
        self.server_owner_id = self.server_data['owner_id']
        self.channels_id = self.get_channels_id()

    def get_channels_id(self):
        return [channel for channel in self.server_data['channels']]

    def get_server_data(self):
        with open(f'{data_folder}data.json') as f:
            return json.load(f)

    def save_data(self, _data):
        with open(f'{data_folder}data.json', 'w') as f:
            json.dump(_data, f, indent=2)

    def get_useful_channel(self, cname):
        return self.client.get_channel(int([channel_id for channel_id in self.channels_id if self.server_data['channels'][str(channel_id)]['cname'] == cname][0]))
        
    def get_server(self, get_id=False):
        return self.client.get_guild(self.server_id)

    def get_owner(self, get_id=False):
        return self.client.get_user(int(self.server_owner_id)) if get_id == False else int(self.server_owner_id)
    
    def get_role(self, cname):
        for role in self.server_data['roles']:
            if self.server_data['roles'][role]['cname'] == cname:
                return discord.utils.get(self.get_server().roles, id=int(role))
            
    def load_config(self):
        with open(f"{data_folder}config.json") as f:
            return json.load(f)
        
    def save_config(self, config):
        with open(f"{data_folder}config.json", 'w') as f:
            json.dump(config, f, indent=2)
