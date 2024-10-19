from utils.guild import GuildInventory
from utils.inventory import Inventory
from utils.item import Item
from utils.ui import EmbedCreator
from utils.pgsql import Query
from decimal import Decimal
from nextcord import Embed, Colour
from enum import Enum

class GameState(int, Enum):
    PLAYING = Colour.blue()
    LOST = Colour.red()
    WON = Colour.green()
    DRAW = Colour.light_gray()
    

class Game():
    def __init__(self, 
                 player: Inventory, 
                 guild: GuildInventory, 
                 wager: float, 
                 sql: Query) -> None:
        self._player = player
        self._guild = guild
        self._wager = wager
        self._sql = sql
        self._gamestate = GameState.PLAYING

    @property
    def player(self):
        return self._player
    
    @player.setter
    def player(self, value: Inventory):
        self._player = value
        
    @property
    def guild(self):
        return self._guild
    
    @guild.setter
    def guild(self, value: GuildInventory):
        self._guild = value
        
    @property
    def wager(self):
        return self._wager
    
    @wager.setter
    def wager(self, value: Decimal):
        self._wager = value
        
    @property
    def gamestate(self):
        """The state of the game using type `GameState`

        Returns:
            `GameState`: The current state of the game
        """
        return self._gamestate
    
    @gamestate.setter
    def gamestate(self, value: GameState):
        if type(value) is not GameState:
            return
        
        self._gamestate = value
        
    def payout(self):
        """Payout the wager if the player won or withdrawl the wager if the player lost and update the user in the database
        """
        if self._gamestate == GameState.WON:
            self._player.deposit(self._wager)
        elif self._gamestate == GameState.LOST:
            self._player.withdraw(self._wager)
        self._sql.update_user(self.guild.guildId, self.player)
        
    def game_embed(self):
        pass
    
    def game_over(self) -> bool:
        """Check if the game is over based on game conditions

        Returns:
            bool: Whether the game is over or not
        """
        pass