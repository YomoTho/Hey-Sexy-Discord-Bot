import json 
from datetime import datetime


data_folder = '../data/'    # This is the path to the 'data' folder is (Where all the json files is)


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
        with open(f'{data_folder}serverDates.json') as f:
            return json.load(f)


    def save_data(self, data):
        with open(f'{data_folder}serverDates.json', 'w') as f:
            json.dump(data, f, indent=4)


    def member_join(self): # This will add 1 when a member joins the server
        self.data[str(self.current_date)]['member_joins'] += 1
        self.save_data(self.data)

    
    def member_leave(self): # This will add 1 when a member leaves the serevr
        self.data[str(self.current_date)]['member_leaves'] += 1
        self.save_data(self.data)


    def on_message(self): # This will add 1 when a message been send
        self.data[str(self.current_date)]['total_messages'] += 1
        self.save_data(self.data)

    
    def get_today_member_leaves(self):  # This will return how many people leaved the server today
        return self.data[str(self.current_date)]['member_leaves']


    def get_today_member_joins(self):   # This will return how many members has joined the server today
        return self.data[str(self.current_date)]['member_joins']


    def get_today_total_messaages(self):    # This will return how many messages has been send today
        return self.data[str(self.current_date)]['total_messages']
    
    
    def cal_total_messages(self):
        total_messages = 0
        for msg in self.data:
            total_messages += self.data[msg]['total_messages']
        else:
            with open(f'{data_folder}data.json') as f:
                server_data = json.load(f)
            
            server_data['total_messages'] = total_messages
            
            with open(f'{data_folder}data.json', 'w') as f:
                json.dump(server_data, f, indent=2)
            
            return total_messages
