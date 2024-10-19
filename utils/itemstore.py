from utils.inventory import Inventory
from utils.item import Item
from typing import List
import json

class ItemStore():
    def __init__(self, guild_id: int, items: List[Item] = None) -> None:
        self._items = items if items is not None else []
        self._guild_id = guild_id
        
    @property
    def guild_id(self):
        return self._guild_id
    
    @guild_id.setter
    def guild_id(self, value: int):
        self._guild_id = value

    @property
    def items(self):
        return self._items
    
    @items.setter
    def items(self, value: List[Item]):
        self._items = value
        
    @property
    def item_count(self):
        return len(self._items)
    
    def get_item(self, id: str) -> Item | None:
        """Get an item within the guilds itemshop

        Args:
            id (str): The id of the item

        Returns:
            Item | None: The item being checked for if exists else None
        """
        for item in self._items:
            if item.id == id:
                return Item(**item.save())
        
        return None
    
    def buy_item(self, item: Item, user: Inventory) -> bool:
        item = Item(**item.save())
        if not user.can_add_item():
            return False
        
        if user.balance < item.value:
            return False
        
        user.withdraw(item.value)
        user.add_item(item)
        return True
        
    def add_item(self, item: Item):
        self._items.append(item)
        
    def add_items(self, items: dict):
        item_list = [Item(**item) for item in items]
        self.items.extend(item_list)
        
    def remove_item(self, id: str) -> bool:
        item = self.get_item(id)
        if item is None:
            return False
        
        self._items.remove(item)
        return True
    
    def save(self):
        return json.dumps([item.save() for item in self.items])
    
    