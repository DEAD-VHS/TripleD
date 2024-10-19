from decimal import Decimal
import random
from typing import Optional, Text, Union
from discord import Interaction
from nextcord import User, TextChannel, Embed
import nextcord
from nextcord.emoji import Emoji
from nextcord.enums import ButtonStyle
from nextcord.interactions import Interaction
from nextcord.partial_emoji import PartialEmoji
from games.game import GameState, Game
from utils.guild import GuildInventory
from utils.inventory import Inventory
from utils.pgsql import Query
from typing import List
import datetime

class BlackjackView(nextcord.ui.View):
    def __init__(self, *, timeout: float | None = 300, auto_defer: bool = True, blackjack: 'Blackjack') -> None:
        super().__init__(timeout=timeout, auto_defer=auto_defer)
        self.game = blackjack
        self.hit_btn = HitButton(game=blackjack)
        self.stand_btn = StandButton(game=blackjack)
        self.ace1_btn = None
        self.ace11_btn = None
        
        if not self.game.game_over():
            self.add_item(self.hit_btn)
            self.add_item(self.stand_btn)
        else:
            self.game.payout()
            return
        
        self.handle_ace()
            
    def handle_ace(self):
        if self.ace11_btn is not None:
            self.children.remove(self.ace11_btn)
            self.ace11_btn = None
        if self.ace1_btn is not None:
            self.children.remove(self.ace1_btn)
            self.ace11_btn = None
            
        ace = self.game.player_hand.has_ace()
        if ace is not None:
            # Button for selecting a value of 1 for Aces
            self.ace1_btn = AceValueButton(custom_id="ace1-select-button", card=ace)
            self.ace11_btn = AceValueButton(custom_id="ace11-select-button", card=ace, value=11)
            self.add_item(self.ace11_btn)
            self.add_item(self.ace1_btn)
            self.hit_btn.disabled = True
            self.stand_btn.disabled = True
        elif self.game.game_over():
            return
        else:
            self.hit_btn.disabled = False
            self.stand_btn.disabled = False
        
class AceValueButton(nextcord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.blurple, label: str | None = None, disabled: bool = False, custom_id: str | None = "ace-value-select", url: str | None = None, 
                 emoji: str | Emoji | PartialEmoji | None = None, 
                 row: int | None = 1, value: int = 1, card: 'Card') -> None:
        label = f'Ace = {value}'
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self._value = value
        self._card = card
        
    async def callback(self, interaction: Interaction) -> None:
        assert self.view is not None
        self.view: BlackjackView
        self.game = self.view.game
        
        self._card.value = self._value
        self._card.is_ace = False
        
        self.game.game_over()
        self.game.payout()
        self.view.handle_ace()
        await interaction.response.edit_message(view=self.view, embed=self.game.game_embed())
        
        
        
class StandButton(nextcord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.secondary, label: str | None = "Stand", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = 2, game: 'Blackjack') -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.game = game
        
    
    async def callback(self, interaction: Interaction) -> None:
        assert self.view is not None
        self.view: BlackjackView
        
        self.view.hit_btn.disabled = True
        self.view.stand_btn.disabled = True
        
        self.game._players_turn = False
        
        self.game.game_over()
        self.game.payout()
        await interaction.response.edit_message(view=self.view, embed=self.game.game_embed())
    
    
class HitButton(nextcord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.green, label: str | None = "Hit", disabled: bool = False, custom_id: str | None = "blackjack-hit-btn", url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = 2, game: 'Blackjack') -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.game = game
        
        
    async def callback(self, interaction: Interaction) -> None:
        self.game.hit()
        if self.game.player_hand.has_ace() is not None:
            self.view.handle_ace()
        
        if self.game.game_over():
            assert self.view is not None
            self.view: BlackjackView
            self.game.payout()
            self.view.hit_btn.disabled = True
            self.view.stand_btn.disabled = True
            
        await interaction.response.edit_message(view=self.view, embed=self.game.game_embed())
        
class Hand():
    def __init__(self, cards: List['Card'] = None) -> None:
        self._cards = cards
        
    @property
    def cards(self):
        return self._cards
    
    def add_card(self, card: 'Card'):
        self._cards.append(card)
    
    @property
    def card_count(self):
        return len(self._cards)
    
    def has_ace(self):
        for card in self._cards:
            if card.is_ace:
                return card
        
        return None
    
    @property
    def value(self):
        return sum([card.value for card in self._cards])
    
    def is_bust(self):
        return self.value > 21
        
    def has_blackjack(self) -> bool:
        if self.card_count > 2:
            return False
        
        ace = self.has_ace()
        if ace is None:
            return False
        
        ace.value = 11
        if self.value == 21:
            return True

        ace.value = 1
        return False
    
    def __str__(self) -> str:
        return " ".join([str(card) for card in self._cards])
        
                

class Card():
    def __init__(self, name: str, value: int, emoji: str) -> None:
        self._name = name
        self._value = value
        self._emoji = emoji
        self._is_ace = True if value == 1 else False
        
    @property
    def is_ace(self):
        return self._is_ace
    
    @is_ace.setter
    def is_ace(self, value: bool):
        self._is_ace = value
    
    @property
    def name(self):
        return self._name
        
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value: int):
        self._value = value
    
    @property
    def emoji(self):
        return self._emoji
    
    def __str__(self) -> str:
        return f'{self.value}{self.emoji}'
    
class Blackjack(Game):
    children = []
    deck = {
    "Ace of Spades": {"emoji": ":spades:", "value": 1},
    "2 of Spades": {"emoji": ":spades:", "value": 2},
    "3 of Spades": {"emoji": ":spades:", "value": 3},
    "4 of Spades": {"emoji": ":spades:", "value": 4},
    "5 of Spades": {"emoji": ":spades:", "value": 5},
    "6 of Spades": {"emoji": ":spades:", "value": 6},
    "7 of Spades": {"emoji": ":spades:", "value": 7},
    "8 of Spades": {"emoji": ":spades:", "value": 8},
    "9 of Spades": {"emoji": ":spades:", "value": 9},
    "10 of Spades": {"emoji": ":spades:", "value": 10},
    "Jack of Spades": {"emoji": ":spades:", "value": 10},
    "Queen of Spades": {"emoji": ":spades:", "value": 10},
    "King of Spades": {"emoji": ":spades:", "value": 10},
    
    "Ace of Hearts": {"emoji": ":hearts:", "value": 1},
    "2 of Hearts": {"emoji": ":hearts:", "value": 2},
    "3 of Hearts": {"emoji": ":hearts:", "value": 3},
    "4 of Hearts": {"emoji": ":hearts:", "value": 4},
    "5 of Hearts": {"emoji": ":hearts:", "value": 5},
    "6 of Hearts": {"emoji": ":hearts:", "value": 6},
    "7 of Hearts": {"emoji": ":hearts:", "value": 7},
    "8 of Hearts": {"emoji": ":hearts:", "value": 8},
    "9 of Hearts": {"emoji": ":hearts:", "value": 9},
    "10 of Hearts": {"emoji": ":hearts:", "value": 10},
    "Jack of Hearts": {"emoji": ":hearts:", "value": 10},
    "Queen of Hearts": {"emoji": ":hearts:", "value": 10},
    "King of Hearts": {"emoji": ":hearts:", "value": 10},
    
    "Ace of Clubs": {"emoji": ":clubs:", "value": 1},
    "2 of Clubs": {"emoji": ":clubs:", "value": 2},
    "3 of Clubs": {"emoji": ":clubs:", "value": 3},
    "4 of Clubs": {"emoji": ":clubs:", "value": 4},
    "5 of Clubs": {"emoji": ":clubs:", "value": 5},
    "6 of Clubs": {"emoji": ":clubs:", "value": 6},
    "7 of Clubs": {"emoji": ":clubs:", "value": 7},
    "8 of Clubs": {"emoji": ":clubs:", "value": 8},
    "9 of Clubs": {"emoji": ":clubs:", "value": 9},
    "10 of Clubs": {"emoji": ":clubs:", "value": 10},
    "Jack of Clubs": {"emoji": ":clubs:", "value": 10},
    "Queen of Clubs": {"emoji": ":clubs:", "value": 10},
    "King of Clubs": {"emoji": ":clubs:", "value": 10},
    
    "Ace of Diamonds": {"emoji": ":diamonds:", "value": 1},
    "2 of Diamonds": {"emoji": ":diamonds:", "value": 2},
    "3 of Diamonds": {"emoji": ":diamonds:", "value": 3},
    "4 of Diamonds": {"emoji": ":diamonds:", "value": 4},
    "5 of Diamonds": {"emoji": ":diamonds:", "value": 5},
    "6 of Diamonds": {"emoji": ":diamonds:", "value": 6},
    "7 of Diamonds": {"emoji": ":diamonds:", "value": 7},
    "8 of Diamonds": {"emoji": ":diamonds:", "value": 8},
    "9 of Diamonds": {"emoji": ":diamonds:", "value": 9},
    "10 of Diamonds": {"emoji": ":diamonds:", "value": 10},
    "Jack of Diamonds": {"emoji": ":diamonds:", "value": 10},
    "Queen of Diamonds": {"emoji": ":diamonds:", "value": 10},
    "King of Diamonds": {"emoji": ":diamonds:", "value": 10}
}

    def __init__(self, player: Inventory, guild: GuildInventory, wager: float, sql: Query) -> None:
        super().__init__(player, guild, wager, sql)
        self._player_hand: Hand = None
        self._dealer_hand: Hand = None
        self.game_deck = []
        self._players_turn = True
        self._dealer_bj = False
        self._player_bj = False
        self._down_card = None
        
        self.game_deck.extend([Card(name=key, **self.deck.get(key)) for key in self.deck.keys()])
        
        random.shuffle(self.game_deck)

        self.setup()

    def setup(self):
        """Setup the blackjack game by giving the player their two cards and the dealer one upcard
        """
        self._player_hand = Hand([self.draw_card(), self.draw_card()])
        self._dealer_hand = Hand([self.draw_card()])
        self._down_card = self.draw_card()
    
    def draw_card(self) -> str:
        """Draw a card from the game deck

        Returns:
            `str`: The card drawn from the deck
        """
        return self.game_deck.pop()
    
    def dealers_turn(self):
        """Run the dealers turn
        """
        self.dealer_hand.add_card(self._down_card)
        while(self.dealer_hand.value < 17):
            self.hit(False)
        
    def hit(self, player: bool = True):
        if player:
            self.player_hand.add_card(self.draw_card())
        else:
            self.dealer_hand.add_card(self.draw_card())
        
    
    def game_over(self) -> bool:
        """Check for game over conditions

        Returns:
            `bool`: Wether the game is over or not
        """
        if self.player_hand.has_blackjack():
            self.dealer_hand.add_card(self._down_card)
            if self.dealer_hand.has_blackjack():
                self.gamestate = GameState.DRAW
                return True
            else:
                self.gamestate = GameState.WON
                self._player_bj = True
                self.wager = round(self.wager * 1.5, 2)
                return True
        
        if self.player_hand.is_bust():
            self.gamestate = GameState.LOST
            return True
        
        if self._players_turn:
            return False
        
        self.dealers_turn()
        
        if self.dealer_hand.has_blackjack():
            self.gamestate = GameState.LOST
            self._dealer_bj = True
            return True
        
        if self.dealer_hand.is_bust():
            self.gamestate = GameState.WON
            return True
        
        if self.dealer_hand.value > self.player_hand.value:
            self.gamestate = GameState.LOST
        elif self.dealer_hand.value < self.player_hand.value:
            self.gamestate = GameState.WON
        else:
            self.gamestate = GameState.DRAW

        return True
        

    @property
    def player_hand(self):
        return self._player_hand

    @property
    def dealer_hand(self):
        return self._dealer_hand
    
    
    def game_embed(self, timestamp=None):
        # Create an embed instance
        embed = Embed(title="Blackjack Game", color=self.gamestate.value)

        # Set the timestamp (if provided, otherwise use current time)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        embed.timestamp = timestamp

        # Add player's hand information using emojis and card values
        embed.add_field(name="Your Hand", value=f"{str(self.player_hand)}\nTotal Value: {self.player_hand.value}", inline=False)

        # Add dealer's upcard information using emojis and card values
        embed.add_field(name="Dealer's Hand", value=f"{str(self.dealer_hand)}\nTotal Value: {self.dealer_hand.value}", inline=False)
        
        if self.gamestate == GameState.WON:
            if self.dealer_hand.is_bust():
                name = "Dealer busted!"
            else:
                name = "Blackjack! You win!" if self._player_bj else "Congrats you win!"
            value = f"You win {Inventory.format_money(self.guild.currency, self.wager)}"
            embed.add_field(name=name, value=value, inline=False)
        elif self.gamestate == GameState.LOST:
            if self.player_hand.is_bust():
                name = "You busted!"
            else:
                name = "The dealer had Blackjack!" if self._dealer_bj else "The dealer has a better hand!"
            value = f"You lose {Inventory.format_money(self.guild.currency, self.wager)}"
            embed.add_field(name=name, value=value, inline=False)
        elif self.gamestate == GameState.DRAW:
            name = "You and the dealer have the same hand, its a draw!"
            value = "Your wager has been returned to you"
            embed.add_field(name=name, value=value, inline=False)

        return embed