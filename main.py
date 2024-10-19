import json
import os
import sys
from discord import ApplicationError, Guild, Interaction, User
from nextcord.ext import commands
import nextcord
from configparser import ConfigParser
from utils.pgsql import Query
import os

from utils.guild import GuildInventory
from utils.inventory import Inventory

TEST_GUILDS = [1001667368801550439]

class InventoryBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_cogs()
        self.pgsql = Query()
        self._guildInventories = {}
    
    def load_cogs(self):
        """
        Loads all cogs in the Cogs folder
        """
        for root, directories, files in os.walk("Cogs"):
            for file in files:
                if file.endswith(".py"):
                    self.load_extension(f"Cogs.{file[:-3]}")
                    
    def get_user_inventory(self, guild_id: int, user: User) -> Inventory:
        """Retrieve a guild members inventory.

        Args:
            guild_id (int): The guilds unique id given by Discord
            member_id (int): The guild members unique id given by Discord

        Returns:
            Inventory: The users inventory for the guild
        """
        guild_inventory = self.get_guild_inventory(guild_id)
        
        inventory = guild_inventory.get_inventory(user)
        if inventory:
            return inventory
        
        data = self.pgsql.get_user(guild_id, user.id)
        
        if data is None:
            inventory = guild_inventory.create_inventory(user)
            self.pgsql.add_user(guild_id, inventory)
        else:
            if 'limit' not in data:
                data['limit'] = guild_inventory.inventory_limit
            inventory = Inventory.load(data, guild_inventory.currency)
                
        guild_inventory.inventories.append(inventory)
        return inventory
    
    def get_currency(self, guild_id: int) -> str:
        """Returns the currency used by the guild

        Args:
            guild_id (int): The unique id of the guild the user is in

        Returns:
            str: The currency symbol
        """
        guild = self.get_guild_inventory(guild_id)
        return guild.currency
    
    def get_guild_inventory(self, guild_id: int) -> GuildInventory:
        """
        Gets the guild inventories

        Parameters
        ----------
        guild : `int`
            The guild id
        
        Returns
        -------
        `GuildInventory`
            The guild inventory or None if it doesn't exist
        """
        guild = self._guildInventories.get(guild_id)
        if guild is not None:
            return guild
        
        guild = self.pgsql.get_guild(guild_id)

        if guild is None:
            guild = self._create_guild_inventory(self.get_guild(guild_id))
        else:
            guild = GuildInventory.load(guild)
        
        self._guildInventories[guild_id] = guild
        
        return guild
        

    def _create_guild_inventory(self, guild: Guild) -> GuildInventory:
        """Creates a new GuildInventory for Guild

        Args:
            guild (Guild): The guild to instantiate

        Returns:
            GuildInventory: The newly created guild
        """
        guild_inventory = GuildInventory(guildId=guild.id, guildName=guild.name)

        self.pgsql.add_guild(guild_inventory)
        
        return guild_inventory
    
    def _create_user_inventory(self, guild: GuildInventory, user: User) -> Inventory:
        """Creates a new user inventory for the guild

        Args:
            guild (GuildInventory): The guild the user is in
            user (User): The user to create the inventory for

        Returns:
            Inventory: The newly created inventory
        """
        inventory = Inventory(user.id, user.name, guild.inventory_limit)
        self.pgsql.add_user(guild_id=guild.guildId,)

    @property
    def guildInventories(self) -> dict[int, GuildInventory]:
        return self._guildInventories
    
    @guildInventories.setter
    def inventories(self, value: dict[int, GuildInventory]) -> None:
        self._guildInventories = value


def _load_config(filename="config.ini", section="discord"):
    parser = ConfigParser()
    parser.read(filename)
    if not parser.has_section(section):
        raise Exception(f'Section {section} not found in the {filename} file')
    
    return dict(parser.items(section)).get('public-key')

def main():
    key = os.getenv('DISCORD_PUBLIC_KEY')
    
    if key is None:
        key = _load_config()
    # Create the bot
    bot = InventoryBot(intents=nextcord.Intents.all(), status=nextcord.Status.online, activity=nextcord.Game("InventoryBot"))

    # Run the bot
    bot.run(key, reconnect=True)

if __name__ == "__main__":
    main()