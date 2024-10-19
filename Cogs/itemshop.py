from nextcord.ext import commands
from nextcord.application_command import slash_command
from nextcord import Interaction, SlashOption
from main import InventoryBot
from utils.item import Item
from utils.ui import EditorView, ItemShopView, EmbedCreator
from main import TEST_GUILDS


class ItemShop(commands.Cog):
    def __init__(self, bot: InventoryBot):
        self.bot = bot
        
    @slash_command(name='shop', description="Opens the item shop where you can purchase items", guild_ids=TEST_GUILDS)
    async def shop(self, interaction: Interaction):
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        user = self.bot.get_user_inventory(guild.guildId, interaction.user)
        if guild.itemShop.item_count == 0:
            await interaction.send(content="There currently are no items available in the itemshop")
            return
        await interaction.response.send_message(view=ItemShopView(guild=guild, sql=self.bot.pgsql, user=user))
    
    @slash_command(name='shopeditor', description="Allows admins to edit the itemshop", guild_ids=TEST_GUILDS)
    async def shopeditor(self, interaction: Interaction):
        pass
    
    @shopeditor.subcommand(name="editor", description="Edit the itemshop within Discord")
    async def editor(self, interaction: Interaction):
        guild = self.bot.get_guild_inventory(interaction.guild_id)
        if guild.itemShop.item_count == 0:
            await interaction.send(content="There currently are not any items available in the itemshop", ephemeral=True)
            return
        await interaction.send(view=EditorView(guild=guild, sql=self.bot.pgsql), ephemeral=True)
    
    @shopeditor.subcommand(name='add', description='Add an item to the itemshop')
    async def add(self, interaction: Interaction, name: str = SlashOption(name="name", description="The name of the item", required=True),
            value: float = SlashOption(name="value", description="The value of the item", required=True, min_value=0),
            description: str = SlashOption(name="description", description="The item description", required=False),
            image_url: str = SlashOption(name="url", description="A url for an image to display for the item", required=False)):

        guild = self.bot.get_guild_inventory(guild_id=interaction.guild_id)
        
        if image_url is not None and not Item.valid_image_url(image_url):
            await interaction.send(content="Invalid URL entered.", ephemeral=True)
            return
        
        new_item = Item(name=name, description=description, value=value, url=image_url)
        
        guild.itemShop.add_item(new_item)
        
        self.bot.pgsql.update_guild(guild)
        await interaction.send(content="Added new item to Item Shop:", embed=EmbedCreator.item_embed(new_item, guild.currency))
        
        

def setup(bot: InventoryBot):
    print(f"Loaded {__name__}")
    bot.add_cog(ItemShop(bot))