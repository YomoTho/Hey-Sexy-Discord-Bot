import discord
try:
    from scripts.data import Data, MyChannel
except ModuleNotFoundError:
    from data import Data, MyChannel




class Leveling_System:
    filename = 'levels.json'

    def __init__(self, member_id: str, exp: int) -> None:
        self.member_id = member_id
        self.exp = exp
        self.level_up = False
        self.from_to_level = None

        if not self.member_id in Data.read(self.filename): # Checks if the member's ID in the json file
            # If the member is not in the json file, then add it
            self.set_member()

        self.current_data = self.get_data()

        self.current_level = self.current_data['lvl']
        self.current_exp = self.current_data['exp']
        self.current_total_exp = self.current_data['total_exp']
        self.before_level = self.current_level
        self.money = self.current_data['money']

        self.end_lvl = self.get_end_lvl()


    def get_data(self) -> dict:
        """
        returns the level, exp, money, of that member (as a dict)
        """
        return Data.read(self.filename)[self.member_id]


    def get_end_lvl(self) -> int:
        """
        returns the end level

        What's end level for? if the exp is more than end level, then level up
        """
        
        end_lvl = int(200)
        if not self.current_level == 0:
            for i in range(self.current_level):
                end_lvl += int(300**1/4)
        return end_lvl


    def set_member(self) -> None:
        with Data.RW(self.filename) as levels:
            levels[self.member_id] = {}
            levels[self.member_id]['exp'] = 0
            levels[self.member_id]['total_exp'] = 0
            levels[self.member_id]['lvl'] = 0
            levels[self.member_id]['money'] = 0 


    def remove_member(self):
        with Data.RW(self.filename) as levels:
            del levels[self.member_id]


    def remove(self) -> None:
        """
        Removing exp from member
        """
        with Data.RW(self.filename) as levels:
            current_value = self.current_exp - self.exp
            res = (current_value - current_value) - current_value
            money_to_remove = int(self.exp / 2)

            while (current_value <= 0):
                self.current_level -= 1
                money_to_remove += 100
                current_value = self.get_end_lvl()
                current_value -= res
                res = (current_value - current_value) - current_value

            if self.current_level < 0:
                self.current_level = 0

            if self.before_level > self.current_level:
                self.level_up = True
                self.from_to_level = '%i -> **%i**' % (self.before_level, self.current_level)

            levels[self.member_id]['lvl'] = self.current_level
            levels[self.member_id]['exp'] = current_value
            levels[self.member_id]['money'] -= money_to_remove
            levels[self.member_id]['total_exp'] -= self.exp

            if levels[self.member_id]['money'] < 0:
                levels[self.member_id]['money'] = 0


    def add(self) -> None:
        """
        Adding exp to member
        """
        with Data.RW(self.filename) as levels:
            self.current_exp += self.exp
            money_to_add = int(self.exp / 3)
            
            while (self.current_exp >= self.end_lvl):
                self.current_level += 1
                money_to_add += (self.current_level * 2)
                self.current_exp = self.current_exp - self.end_lvl
                self.end_lvl = self.get_end_lvl()

            if self.before_level < self.current_level:
                self.level_up = True
                self.from_to_level = '%i -> **%i**' % (self.before_level, self.current_level)

            levels[self.member_id]['lvl'] = self.current_level
            levels[self.member_id]['exp'] = self.current_exp
            levels[self.member_id]['total_exp'] += self.exp
            levels[self.member_id]['money'] += money_to_add


    def buy(self, price:int):
        with Data.RW(self.filename) as levels:
            money = levels[self.member_id]['money']
            
            if money >= price:
                levels[self.member_id]['money'] -= price
                self.money = levels[self.member_id]['money']
            else:
                raise Exception("You don't have enough money. Currently you have $**%i**, but you need $**%i** to buy it." % (money, price))


    def cal_rank(self): # This will return the exp bar, the % and the end lvl     
        per = lambda x,y: int((x / y) * 100) #  x is what % of y

        round = lambda x: int(x / 10) * 10 if (x % 10) < 5 else int((x + 10) / 10) * 10  # Round x to the nearest 10

        end_lvl = self.get_end_lvl()

        p = per(self.current_exp, end_lvl) #  is what % is lvl in end_lvl
        rp = str(round(p))[0] if p < 95 else 10 # rp is p but rounded to the nearest 10, but with the first index of the number (e.p: x = 45; x[0] = 4)
        full_bar = '#' * int(rp)
        empty_bar = ' . ' * int(10 - len(full_bar))

        return full_bar, empty_bar, p, end_lvl


    def rank(self):
        """
        returns: exp, level, total_exp, exp_bar
        """
        rank_data = self.cal_rank() # This will return a exp bar, the % and the end level
        full_bar = rank_data[0]; empty_bar = rank_data[1]; p = rank_data[2]; end_lvl = rank_data[3] # P is for %

        # Here this have multipul string var's 
        rank_message_exp = f"Exp: **{self.current_exp}**/{end_lvl}"   # The user Exp
        rank_message_level = f"[ Level: **{self.current_level}** ]"   # The user Level
        rank_message_total_exp = f"[ Total exp: **{self.current_total_exp}** ] [ Money: $**{self.money}** ]"      # The user total_exp and money
        rank_exp_bar = f"**[{full_bar}{empty_bar}] {p}%**"  # The exp_bar and the %

        return rank_message_exp, rank_message_level, rank_message_total_exp, rank_exp_bar


    def rank_msg(self, member) -> discord.Embed:
        msg = self.rank()
        embed = discord.Embed(
            description=f'{msg[1]}  {msg[2]}\n',
            color=discord.Color.blue()
        )
        embed.add_field(name=msg[3], value=msg[0], inline=False)
        embed.set_author(name=member, icon_url=member.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)
        return embed


    # TODO: Add rank command, and get feedback of shop



    async def send_level_up_msg(self, client, member: discord.Member, title='Level up!'):
        channel = MyChannel(client.level_ups_channel)

        embed = discord.Embed(title=title, description=self.from_to_level, colour=discord.Color.blue())
        embed.set_author(name=member, icon_url=member.avatar_url)

        await channel.send(embed=embed)


    @classmethod
    async def from_message(cls, client, message: discord.Message) -> None:
        level = cls(str(message.author.id), int(len(message.content) / 1.5))
        level.add()

        if level.level_up:
            await level.send_level_up_msg(client, message.author)


    @classmethod
    async def add_exp(cls, client, member: discord.Member, exp:int):
        level = cls(str(member.id), exp)
        level.add()

        if level.level_up:
            await level.send_level_up_msg(client, member)


    @classmethod
    async def remove_exp(cls, client, member: discord.Member, exp:int):
        level = cls(str(member.id), exp)
        level.remove()

        if level.level_up:
            await level.send_level_up_msg(client, member, title='Level down!')

