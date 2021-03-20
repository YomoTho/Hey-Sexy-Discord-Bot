import json


data_folder = '../data/'
expc = 10 # expc stands for: 'every x per coin' (x is exp)
lvl_up_cions = 69 # When a user level up it get this amout of money


class Leveling_System:
    def __init__(self, member):
        self.member = member
        self.users = self.load() # This will get all the users 'Leveling data' like what exp, lvl, money,  they have

    def __add__(self, exp): # This will add exp to the user, and then return True or False if the user leveled up
        self.add_user() # It checks if user exist in the json file, if not then it add the user 
        self.add_exp(exp) 
        
        lvl_up_return = self.lvl_up() # What it return is: {True or False}, {The user (self.member) or 0}, {The user old level or 0}, {The user new level}, {The user exp}
        user_bank = Money(self.member)
        money = user_bank + exp # This is adding money to the user

        self.users[str(self.member.id)]['exp'] = lvl_up_return[4] # Index 4 is exp
        self.users[str(self.member.id)]['lvl'] = lvl_up_return[3] # Index 3 is lvl
        
        if not lvl_up_return[0]:    # It checks if the user leveled up, if so the user will get a bonus
            self.users[str(self.member.id)]['money'] = int(money[0]) # =
            self.users[str(self.member.id)]['r'] = int(money[1])
        else:
            self.users[str(self.member.id)]['money'] = int(money[0]) + (lvl_up_return[5] / expc)
            self.users[str(self.member.id)]['r'] = int(money[1])
            
        self.save(self.users)

        return lvl_up_return[0], lvl_up_return[1], lvl_up_return[2], lvl_up_return[3]


    def rank(self): # It returns the user exp, level, total exp, exp bar, and a bit more
        try:
            self.user_rank_data = self.load()[str(self.member.id)] # Getting the user: exp, level, money, total_exp
        except KeyError:    
            # If the user somehow is not in the json file, It will throw an error
            raise Exception(f"**Error!** Could not find **{self.member}**") 
        else:
            # If no errors, then this will execute:

            self.exp = self.user_rank_data['exp'] # Getting the user exp
            self.lvl = self.user_rank_data['lvl'] # Getting the user level
            self.total_exp = self.user_rank_data['total_exp'] # Getting the user total_exp

            rank_data = self.cal_rank() # This will return a exp bar, the % and the end level
            full_bar = rank_data[0]; empty_bar = rank_data[1]; p = rank_data[2]; end_lvl = rank_data[3] # P is for %

            # Here this have multipul string var's 
            rank_message_1 = f"Exp: **{self.exp}**/{end_lvl}"   # The user Exp
            rank_message_2 = f"[ Level: **{self.lvl}** ]"   # The user Level
            rank_message_3 = f"[ Total exp: **{self.total_exp}** ] [ Money: $**{self.user_rank_data['money']}** ]"      # The user total_exp and money
            rank_exp_bar = f"**[{full_bar}{empty_bar}] {p}%**"  # The exp_bar and the %

            return rank_message_1, rank_message_2, rank_message_3, rank_exp_bar
        
        
    def cal_rank(self): # This will return the exp bar, the % and the end lvl     
        per = lambda x,y: int((x / y) * 100) #  x is what % of y

        round = lambda x: int(x / 10) * 10 if (x % 10) < 5 else int((x + 10) / 10) * 10  # Round x to the nearest 10

        end_lvl = self.get_end_lvl()

        p = per(self.exp, end_lvl) #  is what % is lvl in end_lvl
        rp = str(round(p))[0] if p < 95 else 10 # rp is p but rounded to the nearest 10, but with the first index of the number (e.p: x = 45; x[0] = 4)
        full_bar = '#' * int(rp)
        empty_bar = ' . ' * int(10 - len(full_bar))

        return full_bar, empty_bar, p, end_lvl


    def get_end_lvl(self):  # This will return the 'end_level' of an level
        end_lvl = int(200)
        if not self.lvl == 0:
            for i in range(self.lvl):
                end_lvl += int(300**1/4)
        return end_lvl


    # This will return the users leveling data, like there: exp, level, total_exp and money
    def load(self):
        with open(f'{data_folder}leveling.json', 'r') as f:
            return json.load(f) 


    # This will save changes of the user: exp, level, total_exp, and money
    def save(self, data):
        with open(f'{data_folder}leveling.json', 'w') as f:
            json.dump(data, f, indent=2)


    # Checking if a user is in the leveling.json, if not then we add the user and give it exp, rank, total_exp and rank
    def add_user(self): 
        if not str(self.member.id) in self.users:
            self.users[str(self.member.id)] = {}
            self.users[str(self.member.id)]['exp'] = 0
            self.users[str(self.member.id)]['total_exp'] = 0
            self.users[str(self.member.id)]['lvl'] = 0
            self.users[str(self.member.id)]['money'] = 0
            self.users[str(self.member.id)]['r'] = 0
            self.save(self.users)


    def remove_user(self): # This remove a user from the json file
        del self.users[str(self.member.id)]
        self.save(self.users)


    def add_exp(self, exp):
        self.users[str(self.member.id)]['exp'] += exp
        self.users[str(self.member.id)]['total_exp'] += exp


    def lvl_up(self): # Does check if the exp is more than end_lvl, if so then the user will level up
        self.exp = self.users[str(self.member.id)]['exp']
        self.lvl = self.users[str(self.member.id)]['lvl']

        self.end_lvl = self.get_end_lvl()

        ress, b = 0, 0
        while self.exp >= self.end_lvl:
            if self.exp == self.end_lvl:
                self.lvl += 1
                b = b + (lvl_up_cions * expc)
                self.end_lvl = self.get_end_lvl()
                self.exp = ress
            elif self.exp > self.end_lvl:
                ress = self.exp - self.end_lvl
                self.exp -= ress

        if self.users[str(self.member.id)]['exp'] != self.exp:
            return True, self.member, self.users[str(self.member.id)]['lvl'], self.lvl, self.exp, b
            # Returns True bc the user has level up
    
        self.users[str(self.member.id)]['exp'] = self.exp
        self.users[str(self.member.id)]['lvl'] = self.lvl
        

        #self.save(self.users)

        return False, 0, 0, self.lvl, self.exp
            # 1 = False | It returns False bc the user didn't level up
            # 2 = 0 | It does not need to return member
            # 3 = 0 | It does not need to return the user previous level



class Money(Leveling_System):
    def __init__(self, member):
        self.member = member    # Here it gets the user (member)
        self.users = self.load()  
        self.user_money = self.users[str(self.member.id)]['money'] # This is getting the user amount of money
        self.shop = self.get_shop()
        self.r = self.load()[str(self.member.id)]['r']  # The r stands for "ress"
    
    def __add__(self, income):
        income += self.r
        if income >= expc:
            while income >= expc:
                self.user_money += 1
                income -= expc
        self.r = income

        return self.user_money, self.r
    
    def get_shop(self):
        with open(f'{data_folder}shop.json') as f:
            return json.load(f)

    def buy(self, role=None, liverank=None):
        if not role is None:
            try:
                self.role = self.shop['roles'][str(role.id)]
                self.role_price = self.role['price']
            except KeyError as e:
                print(e)
                raise Exception("Can't buy this role.")
            else:
                if self.user_money >= self.role_price:
                    self.user_money -= self.role_price
                    self.users[str(self.member.id)]['money'] = self.user_money
                    self.save(self.users)
                    return True
                else:
                    return False
        elif not liverank is None:
            with open(f'{data_folder}liverank.json') as f:
                liverank_users = json.load(f)
                
            if not str(self.member.id) in liverank_users:
                liverank_price = 500
                if self.user_money >= liverank_price:
                    yield True
                    self.user_money -= liverank_price
                    self.users[str(self.member.id)]['money'] = self.user_money
                    self.save(self.users)
                    yield True
                else:
                    raise Exception("You already have a live rank.")
            else:
                raise Exception("You don't have enough money to buy a liverank.")
        else:
            raise Exception


    def sell(self, role):
        if role in self.member.roles: # It checks if the user have that role
            if str(role.id) in self.shop['roles']: 
                self.role = self.shop['roles'][str(role.id)]    # Here it getting the role
                self.role_price = self.role['price']    # Here it getting the role price
                self.add = int((self.role_price - ((5 / self.role_price) * 100))) # The Role price - 5%
                self.old_money = self.users[str(self.member.id)]['money']  # Here it define the user money before it got more money
                self.users[str(self.member.id)]['money'] += self.add # Here it's adding the money
                self.new_money = self.users[str(self.member.id)]['money']   # Here it's getting the currnet money of the user
                yield True # Returns True and pause here, after this then it will save and return
                self.save(self.users) # saving
                yield (self.old_money, self.new_money, self.add) # Returns some info of the sell
            else:
                raise Exception("Can't sell this role.")
        else:
            raise Exception("You don't have that role.")


    def remove_money(self):
        pass
    
    # ETC
