from nextcord.ext import commands
from nextcord import Guild
from main import InventoryBot


class Events(commands.Cog):
    def __init__(self, bot: InventoryBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        guild_inventory = self.bot._create_guild_inventory(guild)
        self.bot.guildInventories[guild.id] = guild_inventory
        


def setup(bot: InventoryBot):
    print(f"Loaded {__name__}")
    bot.add_cog(Events(bot))