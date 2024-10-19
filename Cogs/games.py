from operator import inv
import random
import nextcord
from nextcord.ext import commands
from nextcord import SlashOption, Interaction, Permissions
from main import InventoryBot
from games.rps import RPS, RPSView
from games.blackjack import Blackjack, BlackjackView
from utils.inventory import Inventory
from main import TEST_GUILDS

class Games(commands.Cog):
    def __init__(self, bot: InventoryBot) -> None:
        self.bot = bot

    @nextcord.slash_command(name="rps", description="Play a game of Rock, Paper, Scissors against a bot", guild_ids=TEST_GUILDS)
    async def rps(self, 
                  interaction: Interaction, 
                  wager: float = SlashOption(name="bet", description="The amount of money you wish to bet", required=True), 
                  best_of: int = SlashOption(name="rounds", description="How many rounds to play best of", required=False, default=1)):
        
        inventory = self.bot.get_user_inventory(interaction.guild_id, interaction.user)
        
        if inventory.balance < wager:
            await interaction.send("You cannot afford this wager!", ephemeral=True)
            return
        
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        game = RPS(inventory, guild, wager, self.bot.pgsql, best_of)
        await interaction.send(view=RPSView(timeout=300, rps_game=game), embed=game.game_embed())

    
    @nextcord.slash_command(name="coinflip", description="Flip a coin.", guild_ids=TEST_GUILDS)
    async def coinflip(self, interaction: Interaction,
    choice: int = SlashOption(name="choice", description="Your choice", required=True, choices={"heads": 0, "tails": 1}),
    bet: float = SlashOption(name="bet", description="How much to bet", required=False, default=0)):

        guild = self.bot.get_guild_inventory(interaction.guild.id)
        if guild:
            inventory = self.bot.get_user_inventory(interaction.guild_id, interaction.user)
            coin = random.randint(0, 1)
            msg = "Something went wrong!"
            if choice == coin:
                msg = f"You won! It was {'Heads.' if coin == 0 else 'Tails.'}" if bet == 0 else f"It was {'Heads.' if coin == 0 else 'Tails.'} You won {Inventory.format_money(guild.currency, bet)}!"
                inventory.deposit(bet)
            else:
                msg = f"You lost! It was {'Heads.' if coin == 0 else 'Tails.'}" if bet == 0 else f"It was {'Heads.' if coin == 0 else 'Tails.'} You lost {Inventory.format_money(guild.currency, bet)}!"
            
            await interaction.send(msg)
            self.bot.pgsql.update_user(interaction.guild_id, inventory)
            
    @nextcord.slash_command(name="blackjack", description="Play a game of blackjack", guild_ids=TEST_GUILDS)
    async def blackjack(self, interaction: Interaction, wager: float = SlashOption(name="bet", description="How much you want to bet on the game", required=True)):
        
        inventory = self.bot.get_user_inventory(interaction.guild_id, interaction.user)
        
        if inventory.balance < wager:
            await interaction.send("You cannot afford this bet!", ephemeral=True)
            return
        
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        game = Blackjack(inventory, guild, wager, self.bot.pgsql)
        await interaction.send(view=BlackjackView(blackjack=game), embed=game.game_embed())

def setup(bot: InventoryBot):
    print(f"Loaded {__name__}")
    bot.add_cog(Games(bot))
