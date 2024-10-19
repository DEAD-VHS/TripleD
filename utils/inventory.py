from utils.item import Item
import decimal
import json


class Inventory():
    def __init__(self, owner: int, name: str, limit: int = None, items: list[Item] = None, starting_balance: int = 0, currency: str = '$') -> None:
        self._id: int = owner
        self._name: str = name
        self._items: list[Item] = items if items else []
        self._limit = limit
        self._balance = starting_balance
        self._currency = currency
    
    @property
    def id(self) -> int:
        """The owner of the inventory"""
        return self._id
    @property
    def items(self) -> list[Item]:
        return self._items
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def balance(self) -> int:
        """The balance for the player within the guild"""
        return self._balance
    
    @balance.setter
    def balance(self, value: int) -> None:
        self._balance = value
        
    @property
    def currency(self) -> str:
        return self._currency
    
    @currency.setter
    def currency(self, value: str) -> None:
        self._currency = value

    def deposit(self, amount: int) -> bool:
        amount = decimal.Decimal(amount)
        if amount > 0:
            self._balance += amount
            return True
        return False
    
    def withdraw(self, amount: float) -> bool:
        amount = decimal.Decimal(amount)
        if amount > 0 and amount <= self._balance:
            self._balance -= amount
            return True
        return False
    
    def format_balance(self, currency: str) -> str:
        """Returns a formatted string of a users balance"""
        return f"{currency}" + "{:,.2f}".format(self.balance)
    
    
    @staticmethod
    def format_money(currency: str, amount: float) -> str:
        """Returns a formatted balance

        Args:
            currency (str): The currency symbol to use
            balance (float): The balance of the user

        Returns:
            str: The formatted balance
        """

        return f"{currency}" + "{:,.2f}".format(amount)
        
    
    @property
    def find_item(self, name: str) -> Item | None:
        """
        Finds an item in the inventory by name
        
        Parameters
        ----------
        name: :class:`str`
            The name of the item to find
        """
        for item in self._items:
            if item.name == name:
                return item
        return None
    
    @property
    def limit(self) -> int:
        """The maximum number of items the inventory can hold"""
        return self._limit
    
    @limit.setter
    def limit(self, value: int) -> None:
        self._limit = value


    def get_item(self, id: str) -> Item | None:
        """Get a copy of an item from the users inventory

        Args:
            id (str): The id for the item to get

        Returns:
            Item | None: The item if it exists within the users inventory else None
        """
        item = self._get_item(id)
        if item is None:
            return None
        return Item(**self._get_item(id).save())

    
    def _get_item(self, id: str) -> Item | None:
        """A private method for getting the actual item within the users inventory

        Args:
            id (str): The id of the item to get

        Returns:
            Item | None: The item if it exists within the users inventory else None
        """
        for item in self._items:
            if item.id == id:
                return item
            
        return None

    @staticmethod
    def load(data: dict, currency: str) -> 'Inventory':
        """Loads an inventory from json data"""
        return Inventory(owner=data["id"], name=data["name"], limit=data["limit"], items=[Item.load(item, currency) for item in data["items"]], starting_balance=data["balance"], currency=currency)
        
    def save(self) -> dict:
        """Saves the inventory to json data"""
        return {
            "MemberID": self.id,
            "Items": json.dumps([item.save() for item in self._items]),
            "MemberName": self._name,
            "Balance": self._balance
        }
    
    def can_add_item(self) -> bool:
        """Checks if the inventory can add an item"""
        if not self._limit:
            return True
        return len(self.items) < self._limit
    
    def add_item(self, item: Item):
        if item in self._items:
            self.get_item(item.id).amount += item.amount
        else:
            self.items.append(Item(**item.save()))
        
    def remove_item(self, id: str, amount: int = 1) -> bool:
        item = self._get_item(id)
        if item is None:
            return False
        
        if item.amount < amount:
            return False
        
        if item.amount == amount:
            self._items.remove(item)
        else:
            item.amount -= amount
        
    def clear(self) -> None:
        self._items.clear()
    
    def __str__(self) -> str:
        return f"**{self._name}'s Inventory**\n{len(self.items)}/{self.limit if self.limit else '∞'} Items:\n" + "\n".join([f"{item}" for item in self.items])
