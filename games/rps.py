from typing import Optional, Union
import random
from nextcord.emoji import Emoji
from nextcord.enums import ButtonStyle
from nextcord.interactions import Interaction
from nextcord.partial_emoji import PartialEmoji
from utils.guild import GuildInventory
from utils.inventory import Inventory
from utils.pgsql import Query
from .game import Game, GameState
import nextcord
from nextcord import Embed
from enum import Enum

class RPSHand(str, Enum):
    ROCK = 'Rock'
    PAPER = 'Paper'
    SCISSORS = 'Scissors'

class RPSButton(nextcord.ui.Button):
    def __init__(self, *, 
                 style: ButtonStyle = ButtonStyle.secondary, 
                 label: str | None = None, 
                 disabled: bool = False, 
                 custom_id: str | None = "rps-inventory-bot", 
                 url: str | None = None, 
                 emoji: str | Emoji | PartialEmoji | None = None, 
                 row: int | None = 1,
                 hand: RPSHand) -> None:
        label = hand
        self.hand = hand
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    def disable_buttons(self):
        self.view.rock.disabled = True
        self.view.paper.disabled = True
        self.view.scissors.disabled = True
        
    async def callback(self, interaction: Interaction) -> None:
        assert self.view is not None
        
        self.view: RPSView
        game = self.view._game
        
        game._player_hand = self.hand
        
        if not game.next_turn():
            game.payout()
            self.disable_buttons()
            if game.gamestate == GameState.WON:
                await interaction.channel.send(content=f"{interaction.user.mention} just beat AloofBot in Rock, Paper, Scissors and won {Inventory.format_money(game.guild.currency, game.wager)}")
            else:
                await interaction.channel.send(content=f"{interaction.user.mention} just got beat by AloofBot in Rock, Paper, Scissors and lost {Inventory.format_money(game.guild.currency, game.wager)}")
            
        await interaction.response.edit_message(view=self.view, embed=game.game_embed())

class RPSView(nextcord.ui.View):
    def __init__(self, *, timeout: float | None = 180, auto_defer: bool = True, rps_game: 'RPS') -> None:
        super().__init__(timeout=timeout, auto_defer=auto_defer)
        self._game = rps_game
        
        self.rock = RPSButton(style=ButtonStyle.blurple, custom_id=f"{RPSHand.ROCK}-rps-button", hand=RPSHand.ROCK)
        self.paper = RPSButton(style=ButtonStyle.blurple, custom_id=f"{RPSHand.PAPER}-rps-button", hand=RPSHand.PAPER)
        self.scissors = RPSButton(style=ButtonStyle.blurple, custom_id=f"{RPSHand.SCISSORS}-rps-button", hand=RPSHand.SCISSORS)

        self.add_item(self.rock)
        self.add_item(self.paper)
        self.add_item(self.scissors)

        

class RPS(Game):
    def __init__(self, player: Inventory, guild: GuildInventory, wager: float, sql: Query, bestof: int) -> None:
        super().__init__(player, guild, wager, sql)
        # What hand the bot threw for the round
        self._bot_hand = None
        # What hand the player threw for the round
        self._player_hand = None
        # The amount of rounds to play best of against the bot
        self._max_rounds = bestof
        # The current round of the game which starts with round 1
        self._round = 1

        # The amount of wins the bot has
        self._bot_wins = 0
        # The amount of wins the player has
        self._player_wins = 0
        # The previous round results
        self._game_record = []
        
    def _game_record_to_str(self, players_record: bool):
        """Converts the games current record for wins and losses into a string to be used for an :class:`Embed`

        Args:
            players_record (bool): Whether to use the players record or the bots record, which is done by inverting the result

        Returns:
            :class:`str`: The game record in string format  
        """
        if players_record:
            return ' '.join([':white_check_mark:' if win else ':x:' for win in self._game_record])
        else:
            return ' '.join([':white_check_mark:' if not win else ':x:' for win in self._game_record])
        
    def game_embed(self) -> Embed:
        """The Embed that is displayed while playing the game in Discord

        Returns:
            Embed: The Embed to be returned
        """
        embed = Embed(color=self.gamestate.value, title=f"{self.player.name} VS AloofBot in Rock, Paper, Scissors!", description=f"Round {self._round} of {self._max_rounds}")
        embed.add_field(name=f"{self.player.name} Wins", value=self._game_record_to_str(True))
        embed.add_field(name=f"AloofBot Wins", value=self._game_record_to_str(False))

        if self._player_hand is not None:
            embed.add_field(name=f"You chose {self._player_hand.value}", value=f"AloofBot chose {self._bot_hand.value}", inline=False)
            
        if len(self._game_record) == 0 or self.gamestate == GameState.DRAW:
            win_msg = "Draw!"
        else:
            win_msg = "You won!" if self._game_record[len(self._game_record) - 1] else "You lost!"
            
        embed.add_field(name=win_msg, value=" ", inline=False)

        return embed
        
        
    def bots_turn(self):
        """Generates a random choice for the bot
        """
        rps_lookup = [RPSHand.ROCK, RPSHand.PAPER, RPSHand.SCISSORS]
        n = random.randint(0, 2)
        self._bot_hand = rps_lookup[n]
        
    def is_winner(self) -> bool | None:
        """Compares the choices for the player and bot to find which choice wins or if there is a draw

        Returns:
            bool | None: Whether the player is the winner or not
        """
        if self._bot_hand is None or self._player_hand is None:
            return False
        
        if type(self._bot_hand) is not RPSHand or type(self._player_hand) is not RPSHand:
            return False
        
        if self._bot_hand == self._player_hand:
            self.gamestate = GameState.DRAW
            return None
        
        self.gamestate = GameState.LOST
        if self._bot_hand == RPSHand.ROCK and self._player_hand == RPSHand.SCISSORS:
            return False
        if self._bot_hand == RPSHand.PAPER and self._player_hand == RPSHand.ROCK:
            return False
        if self._bot_hand == RPSHand.SCISSORS and self._player_hand == RPSHand.PAPER:
            return False
        
        self.gamestate = GameState.WON
        return True
        
    def next_turn(self):
        """Generates the bots choice, checks if player beat the bot then records the result, then finally checks if the game is over.

        Returns:
            _type_: _description_
        """
        self.bots_turn()
        player_win = self.is_winner()
        
        if player_win is None:
            return True
        
        if self.is_winner():
            self._player_wins += 1
            self._game_record.append(True)
        else:
            self._bot_wins += 1
            self._game_record.append(False)
        
        if self.game_over():
            return False

        self._round += 1
        return True
    
    def game_over(self) -> bool:
        """Check if the current game has reached the win conditions for either player

        Returns:
            bool: Whether the game is over or not
        """
        rounds_remaining = self._max_rounds - self._round

        if rounds_remaining == 0:
            return True
        
        if rounds_remaining < self._player_wins or rounds_remaining < self._bot_wins:
            return True
        
        return False