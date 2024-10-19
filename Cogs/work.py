from main import InventoryBot, TEST_GUILDS
from nextcord.ext import commands
from nextcord.application_command import slash_command
from nextcord import Interaction
import random
from utils.inventory import Inventory

class Income(commands.Cog):

    def __init__(self, bot: InventoryBot) -> None:
        self.bot = bot
        
    
    @slash_command(name="work", description="Get paid for doing some work", guild_ids=TEST_GUILDS)
    async def work(self, interaction: Interaction):
        inventory = self.bot.get_user_inventory(interaction.guild_id, interaction.user)
        amount = random.randint(10000, 100000)
        inventory.deposit(amount)
        
        self.bot.pgsql.update_user(interaction.guild_id, inventory)
        await interaction.send(f"Congrats your hard work paid off! You just received a direct deposit of {Inventory.format_money(self.bot.get_currency(interaction.guild_id), amount)}")
    
        


def setup(bot: InventoryBot) -> None:
    print("Loaded {}".format(__name__))
    bot.add_cog(Income(bot))
