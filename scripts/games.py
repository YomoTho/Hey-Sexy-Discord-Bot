import discord
from random import choice
from levelingSystem import Leveling_System, Money


class TicTacToe:
    def __init__(self, player_1, plaeyr_2):
        self.player_1 = player_1 
        self.player_2 = plaeyr_2
        self.turn = choice([self.player_1, self.player_2]) # This will randomly pick between player 1 and 2 to start first

        self.count = 0 # This will count how many moves has been given
        self.o = ':o2:'     # This is O emoji
        self.x = ':regional_indicator_x:'   # This is the X emoji
        self.empty = ':white_large_square:' # This is just white emoji 
        self.gameBoard = [[self.empty, self.empty, self.empty], [self.empty, self.empty, self.empty], [self.empty, self.empty, self.empty]]
        self.game_msg = None    # This is the game message 
        self.whos_turn_msg = None   # This is the 'who's turn is it' message
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'] # All the reactions, that the players can react to
        self.move_choice = {
            '1️⃣': '0:0',
            '2️⃣': '0:1',
            '3️⃣': '0:2',
            '4️⃣': '1:0',
            '5️⃣': '1:1',
            '6️⃣': '1:2',
            '7️⃣': '2:0',
            '8️⃣': '2:1',
            '9️⃣': '2:2'
        }
        self.someone_won = False


    async def print(self):
        return '\n'.join([''.join(line) for line in self.gameBoard])


    async def move(self, emoji):
        try:
            if self.turn.bot:
                while True:
                    try:
                        move_pos = self.move_choice[emoji].split(':')
                        self.gameBoard[int(move_pos[0])][int(move_pos[1])] = self.o if self.turn == self.player_1 else self.x
                        del self.move_choice[emoji]
                        break
                    except KeyError:
                        emoji = choice(self.reactions)
            else:
                move_pos = self.move_choice[emoji.name].split(':')
                self.gameBoard[int(move_pos[0])][int(move_pos[1])] = self.o if self.turn == self.player_1 else self.x
                del self.move_choice[emoji.name]
            
            await self.game_msg.edit(content=await self.print())

            self.count += 1

            if self.count >= 3:
                who_won = await self.check_who_won()
                if who_won[0]:
                    self.someone_won = True
                    winner = Leveling_System(who_won[1])
                    w = winner + 100 # If a user win then the user get 100 exp
                    embed = discord.Embed(description=f"**{who_won[1]}** won!!!" if not w[0] else f"**{who_won[1]}** won!!!\nLeveled up from {w[2]} -> {w[3]}")
                    await self.whos_turn_msg.edit(embed=embed)
                    return

            if self.turn == self.player_1:
                self.turn = self.player_2
            else:
                self.turn = self.player_1

            if self.count >= 9:
                embed = discord.Embed(description=f"Tie")
            else:
                embed = discord.Embed(description=f"**{self.turn.name}** turn")

            await self.whos_turn_msg.edit(embed=embed)
            
            if self.turn.bot:
                await self.move(choice(self.reactions))
        except KeyError:
            pass


    async def check_who_won(self):
        # H check
        board = '\n'.join([''.join(line) for line in self.gameBoard]).split('\n')
        for line in board:
            if line == self.x * 3:  # X = player 2
                return True, self.player_2
            elif line == self.o * 3:    # O = player 1
                return True, self.player_1

        # V check
        v_gb = [['0', '0', '0'], ['0', '0', '0'], ['0', '0', '0']]
        for l_idx, line in enumerate(self.gameBoard):
            for g_idx, grid in enumerate(line):
                v_gb[g_idx][l_idx] = grid
        else:
            v = '\n'.join([''.join(line) for line in v_gb]).split('\n')
            for line in v:
                if line == self.x * 3:
                    return True, self.player_2
                elif line == self.o * 3:
                    return True, self.player_1

            if self.gameBoard[1][1] == self.x:
                if self.gameBoard[0][0] == self.x and self.gameBoard[2][2] == self.x:
                    return True, self.player_2
                elif self.gameBoard[0][2] == self.x and self.gameBoard[2][0] == self.x:
                    return True, self.player_2
            elif self.gameBoard[1][1] == self.o:
                if self.gameBoard[0][0] == self.o and self.gameBoard[2][2] == self.o:
                    return True, self.player_1
                elif self.gameBoard[0][2] == self.o and self.gameBoard[2][0] == self.o:
                    return True, self.player_1
            return False, 0
