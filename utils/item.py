import json
from uuid import UUID
import uuid
import re

class Item():
    def __init__(self, name: str, description: str, value: float, currency: str = '$', id: UUID = None, amount: int = 1, url: str = None) -> None:
        self._name = name
        self._description = description
        self._value = value
        self._id = id if id is not None else str(uuid.uuid4())
        self._currency = currency
        self._amount = int(amount)
        self._url = url

    @property
    def name(self) -> str:
        """The items name"""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        
    @property
    def url(self):
        return self._url
    
    @url.setter
    def url(self, value: str):
        self._url = value

    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value: str):
        self._id = value
    
    @property
    def description(self) -> str:
        """The items description"""
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        
    @property
    def amount(self) -> int:
        """How many of this item there are

        Returns:
            int: The amount of items
        """
        return self._amount
        
    @amount.setter
    def amount(self, value: int) -> None:
        self._amount = value
        
    def inc_amount(self, amount: int) -> None:
        self._amount += amount
    
    @property
    def value(self) -> str:
        """The items value"""
        return self._value
    
    @value.setter
    def value(self, value: int) -> None:
        self._value = value

    @staticmethod
    def load(data: dict, currency: str) -> 'Item':
        return Item(**data, currency=currency)
    
    def toJSON(self):
        return json.dumps(self, default= lambda o: o.__dict__, sort_keys=True)
    
    def save(self) -> dict:
        return {
            "name": self._name,
            "description": self._description,
            "value": self._value,
            "id": str(self._id),
            "amount": self._amount,
            "url": self._url
        }
        
    @staticmethod
    def valid_image_url(url: str):
        if re.match(r'(?:([^:/?#]+):)?(?:\/\/([^/?#]*))?([^?#]*\.(?:jpg|gif|png))(?:\?([^#]*))?(?:#(.*))?', url):
            return True
        return False
        
        
    def _is_valid_operand(self, other: object):
        return (hasattr(other, "id"))
    
    def __eq__(self, other: object) -> bool:
        if self._is_valid_operand(other):
            return other.id == self.id
        return False

    def __repr__(self):
        return self.name
    
    def __str__(self):
        return f"{self._name}: {self._description}\nValue: {self._currency}" + "{:,.2f}".format(self._value)