from nextcord.ext import commands
from main import InventoryBot
from nextcord.application_command import slash_command
from nextcord import Interaction, SlashOption, Permissions, User
from utils.inventory import Inventory
from decimal import Decimal
from main import TEST_GUILDS

class Economy(commands.Cog):

    def __init__(self, bot: InventoryBot) -> None:
        self.bot = bot

    @slash_command(name="balance", description="View your balance", guild_ids=TEST_GUILDS)
    async def balance(self, interaction: Interaction, user: User = SlashOption(name="user", description="The user to check the balance of", required=False)):
        user = user if user is not None else interaction.user
        inventory: Inventory = self.bot.get_user_inventory(interaction.guild.id, user)
        if inventory is None:
            await interaction.response.send_message("Could not find inventory", ephemeral=True)

        await interaction.response.send_message(("Your" if user == interaction.user else user.name + '\'s') + f" balance is {inventory.format_balance(self.bot.get_currency(interaction.guild_id))}", ephemeral=True)
        

    def _format_top_balances(self, currency: str, users: list[dict]) -> str:
        """Formats a top balance list

        Args:
            users (tuple[Inventory]): The top users

        Returns:
            str: The formated top balance list
        """
        rankings = []
        i = 1
        for user in users:
            rankings.append(f"{i}.) {user['name']} - {Inventory.format_money(currency, user['balance'])}")
            i += 1
        return '\n'.join(rankings)

    @slash_command(name="balancetop", description="View the top 10 balances", guild_ids=TEST_GUILDS)
    async def balancetop(self, interaction: Interaction):
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        if guild:
            top_users = self.bot.pgsql.get_top_balances(interaction.guild_id, 10)
            await interaction.response.send_message(self._format_top_balances(guild.currency, top_users), ephemeral=False)
    
    @slash_command(name="addmoney", description="Add money to your balance", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def addmoney(self, interaction: Interaction, amount: float = SlashOption(name="amount", description="The amount of money to add", required=True), username: User = SlashOption(name="user", description="The user to add the money to", required=False)):
        amount = Decimal(round(amount, 2))
        user = interaction.user if not username else username
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        inventory = self.bot.get_user_inventory(interaction.guild_id, user)

        if inventory is None:
            await interaction.response.send_message("Could not find inventory", ephemeral=True)
        
        if not inventory.deposit(amount):
            await interaction.response.send_message(f"Something went wrong.", ephemeral=True)
            return

        msg = f"Added {Inventory.format_money(guild.currency, amount)} to your balance" if user == interaction.user else f"Added {amount} to {user.name}'s balance"
        self.bot.pgsql.update_user(interaction.guild_id, inventory)
        await interaction.response.send_message(msg, ephemeral=True)
        
        
    @slash_command(name="removemoney", description="Remove money from your balance", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def removemoney(self, interaction: Interaction, amount: float = SlashOption(name="amount", description="The amount of money to remove", required=True), username: User = SlashOption(name="user", description="The user to remove the money from", required=False)):
        amount = Decimal(round(amount, 2))
        user = interaction.user if not username else username
        guild = self.bot.get_guild_inventory(interaction.guild.id)
        
        if guild:
            inventory = guild.get_inventory(user)
            if inventory:
                if inventory.withdraw(amount):
                    self.bot.pgsql.update_user(interaction.guild_id, inventory)
                    msg = f"Removed {Inventory.format_money(guild.currency, amount)} from your balance" if user == interaction.user else f"Removed {amount} from {user.name}'s balance"
                    await interaction.response.send_message(msg, ephemeral=True)
                    return
                else:
                    await interaction.response.send_message("You don't have enough money", ephemeral=True)
                    return
        await interaction.response.send_message("Could not find inventory", ephemeral=True)

    @slash_command(name="setbalance", description="Set the balance of a player", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def setbalance(self, interaction: Interaction, user: User = SlashOption(name="user", description="The user to set the balance of", required=True, verify=True), amount: float = SlashOption(name="amount", description="The amount to set the balance to", required=True)):
        amount = Decimal(round(amount, 2))
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        if guild is None:
            await interaction.send(content="No guild found", ephemeral=True)
            return
        
        inventory = self.bot.get_user_inventory(interaction.guild_id, user)
        if inventory is None:
            await interaction.send(content="No user found!", ephemeral=True)
            return
        
        inventory.balance = amount
        self.bot.pgsql.update_user(interaction.guild_id, inventory)
        await interaction.send(f"Set {user.mention}'s balance to {inventory.format_balance(guild.currency)}", ephemeral=True)
        
    @slash_command(name="pay", description="Send another player some money", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def pay(self, 
                  interaction: Interaction, 
                  user: User = SlashOption(name="user", description="The user to send the money to", required=True), 
                  amount: float = SlashOption(name="pay", description="The amount of money to send", required=True)):
        
        inventory_sender = self.bot.get_user_inventory(interaction.guild_id, interaction.user)
        if not inventory_sender.withdraw(amount):
            await interaction.send(f"You do not have enough money to send {Inventory.format_money(inventory_sender.currency, amount)} to {user.name}")
        
        inventory_receiver = self.bot.get_user_inventory(interaction.guild_id, user)

        
        inventory_receiver.deposit(amount)
        
        self.bot.pgsql.update_user(interaction.guild_id, inventory_sender)
        self.bot.pgsql.update_user(interaction.guild_id, inventory_receiver)
        await interaction.send(content=f"{interaction.user.mention} sent {user.mention} {Inventory.format_money(inventory_sender.currency, amount)}")
        
        
        
                
    @slash_command(name="setcurrency", description="Set the currency for the server", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def setcurrency(self, interaction: Interaction, currency: str = SlashOption(name="currency", description="The currency to use for the server", required=True, max_length=5)):
        guild = self.bot.get_guild_inventory(guild_id=interaction.guild_id)
        guild.currency = currency
        self.bot.pgsql.update_guild(guild)
        await interaction.send(content="Successfully changed guild currency to {}".format(guild.currency))


def setup(bot: InventoryBot) -> None:
    print("Loaded {}".format(__name__))
    bot.add_cog(Economy(bot))


