from discord import User
from utils.inventory import Inventory
from utils.item import Item
from utils.itemstore import ItemStore
import json

class GuildInventory():
    def __init__(self, guildId: int, guildName: str, inventory_size: int = None, inventories: list[Inventory] = None, currency: str = "$", items: list[Item] = None) -> None:
        self._inventory_limit = inventory_size
        self._guildId = guildId
        self._guildName = guildName
        self._inventories: list[Inventory] = inventories if inventories else []
        self._itemshop = ItemStore(guildId, items)
        self._currency = currency
    
    @property
    def guildId(self) -> int:
        return self._guildId
    
    @property
    def guildName(self) -> str:
        return self._guildName
    
    @property
    def inventories(self) -> list:
        return self._inventories
    
    @property
    def itemShop(self):
        """The items available for purchase within the guild for users

        Returns:
            list[Item]: The items available for purchase within the guild
        """
        return self._itemshop
    
    @property
    def inventory_limit(self) -> int:
        """The limit for items the guild allows a user to possess 

        Returns:
            int: _description_
        """
        return self._inventory_limit
    
    @inventory_limit.setter
    def inventory_limit(self, value: int) -> None:
        self._inventory_limit = value
        for inventory in self._inventories:
            inventory.limit = value
    
    @property
    def currency(self) -> str:
        """The currency used by this guild (defaults to $)

        Returns:
            str: The currency of the guild
        """
        return self._currency

    @currency.setter
    def currency(self, value: str) -> None:
        self._currency = value
        for inventory in self._inventories:
            inventory.currency = value

    @staticmethod
    def load(data: dict) -> 'GuildInventory':
        inventories, itemshop = None, None
        if data.get('inventories'):
            inventories = [Inventory.load(inventory) for inventory in data["inventories"]]
        if data.get('itemshop') is not None:
            itemshop = [Item(**item) for item in data.get('itemshop')]
        return GuildInventory(data["guildId"], data["guildName"], data["inventory_limit"], inventories, data["currency"], itemshop)
        
    def can_buy_item(self, item: Item, user: Inventory) -> bool:
        """Check for whether the user can afford the item they are trying to purchase

        Args:
            item (Item): The item being purchased
            user (Inventory): The user purchasing the item

        Returns:
            bool: Whether the user can purchase the item or not
        """
        if user.balance >= item.value:
            return True
        
        return False
    
    def toJSON(self) -> str:
        return json.dumps(self.save())

    def get_inventory(self, user: User) -> Inventory:
        for inventory in self._inventories:
            if inventory.id == user.id:
                return inventory
        print(f"Could not find inventory for {user.name} ({user.id})")
        return None
    
    def get_baltop(self) -> list:
        return sorted(self._inventories, key=lambda x: x.balance, reverse=True)[:10]
    
    def create_inventory(self, owner: User) -> Inventory:
        inventory = Inventory(owner=owner.id, name=owner.name, limit=self.inventory_limit)
        self._inventories.append(inventory)
        return inventory

    def remove_inventory(self, owner: User) -> bool:
        inventory = self.get_inventory(owner)
        if inventory:
            self.inventories.remove(inventory)
            return True
        else:
            return False

    def save(self) -> dict:
        return {
            "guild_id": self.guildId,
            "guild_name": self.guildName,
            "currency": self.currency,
            "inventory_limit": self.inventory_limit,
            "itemshop": self.itemShop.save()
        }

    def __str__(self) -> str:
        return f"Guild: {self._guildName} ({self._guildId}) - Inventories: {[inv for inv in self._inventories]}"