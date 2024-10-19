from discord import Interaction, SlashCommandOption, SlashOption
from nextcord import Permissions, User
from nextcord.ext import commands
from nextcord.application_command import slash_command
from main import InventoryBot
from utils.item import Item
from utils.ui import EmbedCreator, EditUserInventoryView, ItemSelectorType
from main import TEST_GUILDS

class InventoryCmd(commands.Cog):
    def __init__(self, bot: InventoryBot):
        self.bot = bot
    
    
    @slash_command(name="inventory", description="View your inventory", guild_ids=TEST_GUILDS)
    async def inventory(self, interaction: Interaction, user: User = SlashOption(name="user", description="The user to view the inventory of", required=False)):
        inventory = self.bot.get_user_inventory(interaction.guild_id, user if user is not None else interaction.user)
        embeds = EmbedCreator.many_item_embeds(inventory.items, inventory.currency)
        if len(inventory.items) == 0:
            await interaction.send(content="There are no items to show", ephemeral=True)
            return
        
        if user is not None:
            await interaction.response.send_message(f"Viewing {user.name}'s inventory", embeds=embeds)
            return
        else:
            await interaction.response.send_message(content=f"**{inventory.name}'s Inventory**", embeds=embeds)


    @slash_command(name="additem", description="Add an item to your inventory", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def additem(self, interaction: Interaction, user: User = SlashOption(name="user", description="The user to give the item", required=True)):
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        user = self.bot.get_user_inventory(guild.guildId, user)
        
        if guild.itemShop.item_count == 0:
            await interaction.send(content="There are no available items in the guilds item shop!", ephemeral=True)
            return
        
        if guild is None or user is None:
            await interaction.send(content="Inventory not found for user: {}".format(user.name))
            return
        
        await interaction.send(view=EditUserInventoryView(user=user, guild=guild, selectorType=ItemSelectorType.ADD_ITEM, sql=self.bot.pgsql))
        

    @slash_command(name="removeitem", description="Remove an item from your inventory", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def removeitem(self, interaction: Interaction, user: User = SlashOption(name="user", description="The user to remove an item from", required=True)):
        inventory = self.bot.get_user_inventory(interaction.guild_id, user)
        guild = self.bot.get_guild_inventory(interaction.guild.id)

        if guild is None or inventory is None:
            await interaction.send(content="Something went wrong!", ephemeral=True)
            return

        
        if len(inventory.items) == 0:
            await interaction.send(content="This user has not items to remove.", ephemeral=True)
            return
        
        await interaction.send(view=EditUserInventoryView(user=inventory, guild=guild, selectorType=ItemSelectorType.REMOVE_ITEM, sql=self.bot.pgsql))
        

    @slash_command(name="clearinventory", description="Clear your or another users inventory", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def clearinventory(self, interaction: Interaction, username: User = SlashOption(name="user", description="The user to clear the inventory of", required=False)):
        user = interaction.user if not username else username
        inventory = self.bot.get_user_inventory(interaction.guild_id, user)
        
        if inventory is None:
            await interaction.send(content="No inventory found!")
            return
        
        inventory.clear()
        self.bot.pgsql.update_user(interaction.guild_id, inventory)
        
        msg = f"Your inventory has been cleared" if user == interaction.user else f"{user}'s inventory has been cleared"
        await interaction.response.send_message(msg, ephemeral=True)
        
        
    @slash_command(name="maxitems", description="Set the max items for the guild", guild_ids=TEST_GUILDS, default_member_permissions=Permissions(administrator=True))
    async def maxitems(self, interaction: Interaction, maxitems: int = SlashOption(name="maxitems", description="The max items to set", required=True)):
        guild = self.bot.get_guild_inventory(interaction.guild.id)

        if guild is None:
            await interaction.send(content="Something went wrong!")
            return
        
        guild.inventory_limit = maxitems
        self.bot.pgsql.update_guild(guild)
        
        await interaction.response.send_message(f"Set max items to {maxitems}", ephemeral=True)
        
        
def setup(bot: InventoryBot):
    print(f"Loaded {__name__}")
    bot.add_cog(InventoryCmd(bot))