import json


data_folder = '../data/'


class Leveling_System:
    def __init__(self, member):
        self.member = member
        self.users = self.load_leveling_json()

    def __add__(self, exp): # This will add exp to the user, and then return True or False if the user leveled up
        self.add_user() # It checks if user id exist in the json file, if not then it add the user 
        self.add_exp(exp)
        
        print(f'{self.member} + {exp} exp')
        
        lvl_up_return = self.lvl_up() # What it return is: {True or False}, {The user (self.member) or 0}, {The user old level or 0}, {The user new level}, {The user exp}

        self.users[str(self.member.id)]['exp'] = lvl_up_return[4] # Index 4 is exp
        self.users[str(self.member.id)]['lvl'] = lvl_up_return[3] # Index 3 is lvl

        self.dump_leveling_json(self.users)

        return lvl_up_return[0], lvl_up_return[1], lvl_up_return[2], lvl_up_return[3]


    def rank(self): # It returns the user exp, level, total exp, exp bar, and a bit more
        try:
            self.user_rank_data = self.load_leveling_json()[str(self.member.id)]
        except KeyError:
            raise Exception(f"**Error!** Could not find **{self.member}**")
        else:
            self.exp = self.user_rank_data['exp']
            self.lvl = self.user_rank_data['lvl']
            self.total_exp = self.user_rank_data['total_exp']

            rank_data = self.cal_rank()
            full_bar = rank_data[0]; empty_bar = rank_data[1]; p = rank_data[2]; end_lvl = rank_data[3] # P is for %

            rank_message_1 = f"Exp: **{self.exp}**/{end_lvl}"
            rank_message_2 = f"Level: **{self.lvl}**"
            rank_message_3 = f"Total exp: **{self.total_exp}**"
            rank_exp_bar = f"[**{full_bar}**{empty_bar}] {p}%"

            return rank_message_1, rank_message_2, rank_message_3, rank_exp_bar
        
        
    def cal_rank(self):        
        per = lambda x,y: int((x / y) * 100)

        def round(x):
            rem = x % 10
            if rem < 5:
                x = int(x / 10) * 10
            else:
                x = int((x + 10) / 10) * 10
            return x

        end_lvl = self.get_end_lvl()

        p = per(self.exp, end_lvl) #  is what % is lvl in end_lvl
        rp = str(round(p))[0] if p < 95 else 10 # rp is p but rounded to the nearest 10
        full_bar = '#' * int(rp)
        empty_bar = '=' * int(10 - len(full_bar))

        return full_bar, empty_bar, p, end_lvl


    def get_end_lvl(self):
        end_lvl = int(100)
        if not self.lvl == 0:
            for i in range(self.lvl):
                end_lvl += int(150**1/4)
        return end_lvl


    def load_leveling_json(self):
        with open(f'{data_folder}leveling.json', 'r') as f:
            return json.load(f) 


    def dump_leveling_json(self, data):
        with open(f'{data_folder}leveling.json', 'w') as f:
            json.dump(data, f, indent=2)


    # Checking if a user is in the leveling.json, if not then we add the user and give it exp, rank, total_exp and rank, then return True
    def add_user(self): 
        if not str(self.member.id) in self.users:
            self.users[str(self.member.id)] = {}
            self.users[str(self.member.id)]['exp'] = 0
            self.users[str(self.member.id)]['total_exp'] = 0
            self.users[str(self.member.id)]['lvl'] = 0


    async def remove_user(self): # This remove a user from the json file
        del self.users[str(self.member.id)]
        self.dump_leveling_json(self.users)


    def add_exp(self, exp):
        self.users[str(self.member.id)]['exp'] += exp
        self.users[str(self.member.id)]['total_exp'] += exp


    def lvl_up(self): # Does check if the exp is more than end_lvl, if so then the user will level up
        self.exp = self.users[str(self.member.id)]['exp']
        self.lvl = self.users[str(self.member.id)]['lvl']

        self.end_lvl = self.get_end_lvl()

        ress = 0
        while self.exp >= self.end_lvl:
            if self.exp == self.end_lvl:
                self.lvl += 1
                self.end_lvl = self.get_end_lvl()
                self.exp = ress
            elif self.exp > self.end_lvl:
                ress = self.exp - self.end_lvl
                self.exp -= ress


        if self.users[str(self.member.id)]['exp'] != self.exp:
            return True, self.member, self.users[str(self.member.id)]['lvl'], self.lvl, self.exp
            # Returns True bc the user has level up
    
        self.users[str(self.member.id)]['exp'] = self.exp
        self.users[str(self.member.id)]['lvl'] = self.lvl

        self.dump_leveling_json(self.users)

        return False, 0, 0, self.lvl, self.exp
            # 1 = False | It returns False bc the user didn't level up
            # 2 = 0 | It does not need to return member
            # 3 = 0 | It does not need to return the user previous level



class Money(Leveling_System): # Money cold: "Sexy Coin"
    def __init__(self, total_exp):
        self.total_exp = total_exp
        
    def bank(self, member):
        pass #TODO: make money system and this will be the bank, the bank should do: return how much money they have and stuff like that
    
    def buy(self):
        pass
    
    def sell(self):
        pass
    
    def add_money(self):
        pass
    
    def remove_money(self):
        pass
    
    # ETC
