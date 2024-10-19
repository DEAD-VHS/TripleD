from psycopg2.extensions import connection, cursor
import psycopg2
from configparser import ConfigParser
from typing import List, Dict
from utils.inventory import Inventory
from utils.guild import GuildInventory
import os

class Query():
    def __init__(self) -> None:
        self._connect()
        
    def _config(self, filename='config.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        db = {}
        
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            db['host'] = os.getenv('HOST')
            db['database'] = os.getenv('DATABASE')
            db['user'] = os.getenv('USER')
            db['password'] = os.getenv('PASSWORD')
            # raise Exception('Section {0} not found in the {1} file'.format(section, filename))
        
        return db

    def _connect(self):
        conn = None
        try:
            params = self._config()
            
            print("Connecting to PostgreSQL database...")
            conn: connection = psycopg2.connect(**params)
            cur: cursor = conn.cursor()
            
            print('PostgreSQL database version: ')
            cur.execute('SELECT version()')
            
            db_version = cur.fetchone()
            print(db_version)
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        if conn is not None:
            self.conn = conn
    
    def add_guild(self, guild: GuildInventory):
        """Add a guild to Guilds table

        Args:
            guild_id (int): The id of the guild given by discord
            guild_name (str): The name of the guild
            inventories (str): The inventories of the users within the guild
        """        
        sql = """
        create table if not exists Guilds(
            GuildID bigint PRIMARY KEY,
            GuildName varchar(255),
            Currency varchar(10),
            MaxInventory integer,
            ItemShop json
        );
        
        insert into Guilds(GuildID, GuildName, Currency, MaxInventory, ItemShop) 
        values (%(guild_id)s, %(guild_name)s, %(currency)s, %(inventory_limit)s, %(itemshop)s);
        
        create table if not exists Guild%(guild_id)s(
            MemberID bigint PRIMARY KEY,
            MemberName varchar(255),
            Balance decimal(65, 2),
            Inventory json
        );
        """
        cur = self.conn.cursor()
        
        cur.execute(sql, guild.save())
        
        self.conn.commit()
        cur.close()
    
    def get_guild(self, guild_id: int):
        """Retrieve a guilds user inventories from the database

        Args:
            guild_id (int): The id of the guild given by Discord
        """
        sql = """
        CREATE TABLE IF NOT EXISTS Guilds(
            GuildID bigint PRIMARY KEY,
            GuildName varchar(255),
            Currency varchar(10),
            MaxInventory integer,
            itemshop json
        );
        
        SELECT * FROM Guilds WHERE GuildID = %s;
        """
        cur = self.conn.cursor()
        
        cur.execute(sql, (guild_id,))
        
        result = cur.fetchone()
        cur.close()
        if result is None:
            return None
        
        return { 'guildId': result[0], 'guildName': result[1], 'currency': result[2], 'inventory_limit': result[3], 'itemshop': result[4] }
        
    def update_guild(self, guild: GuildInventory):
        
        sql = """
        UPDATE guilds
        SET GuildName = %(guild_name)s,
            Currency = %(currency)s,
            MaxInventory = %(inventory_limit)s,
            itemshop = %(itemshop)s
        WHERE guildid = %(guild_id)s
        """
        cur = self.conn.cursor()
        
        cur.execute(sql, guild.save())
        self.conn.commit()
        
        cur.close()
        
    def add_user(self, guild_id: int, inventory: Inventory):
        """Add user to guild database

        Args:
            guild_id (int): The guild to add the user to
            user_id (int): The unique id for the user being added
            balance (float): The users balance for the guild
            items (Dict): The users items within the guild
        """
        
        sql = """
        insert into Guild%(guild_id)s(MemberID, MemberName, Balance, Inventory) 
        values(%(MemberID)s, %(MemberName)s, %(Balance)s, %(Items)s);
        """
        cur = self.conn.cursor()
        
        cur.execute(sql, {"guild_id": guild_id, **inventory.save()})
        
        self.conn.commit()
        cur.close()
        
    def get_user(self, guild_id: str, user_id: str):
        sql = """
        select MemberID, MemberName, Balance, Inventory 
        from Guild%s 
        where MemberID = %s;
        """
        
        cur = self.conn.cursor()
        cur.execute(sql, (guild_id, user_id,))
        result = cur.fetchone()
        if result:
            return { 'id': result[0], 'name': result[1], 'balance': result[2], 'items': result[3] }
        
        return None
    
    def get_balance(self, guild_id, user_id):
        sql = """
        select Balance from Guild%s where MemberID = %s;
        """
        cur = self.conn.cursor()
        cur.execute(sql, (guild_id, user_id,))
        result = cur.fetchone()
        print(result)
        return result
    
    def get_top_balances(self, guild_id: int, count: int) -> List[Inventory]:
        """Get the top n balances within the guild

        Args:
            guild_id (int): The guild to get the top balances in
            count (int): The amount of balances to retrieve

        Returns:
            List[Inventory]: The top balances
        """
        sql = """
        SELECT MemberName, Balance FROM Guild%s
        ORDER BY Balance DESC
        FETCH FIRST %s ROWS ONLY 
        """
        cur = self.conn.cursor()
        cur.execute(sql, (guild_id, count,))
        
        result = cur.fetchall()
        result = [{ 'name': balance[0], 'balance': balance[1] } for balance in result]
        cur.close()

        return result
    
    def update_user(self, guild_id: int, inventory: Inventory):
        """Update a user within the database

        Args:
            guild_id (`str`): The id for the guild the user is in
            user_id (`str`): The unique id for the user within discord
            userdata (`Dict`): the data to be updated
        """
        
        sql = """
        UPDATE Guild%(guild_id)s
        SET Balance = %(Balance)s,
            Inventory = %(Items)s
        WHERE MemberID = %(MemberID)s
        """
        cur = self.conn.cursor()
        
        cur.execute(sql, {"guild_id": guild_id, **inventory.save()})
        self.conn.commit()
        cur.close()
        