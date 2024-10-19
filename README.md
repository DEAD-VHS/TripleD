# Inventory Bot
A Discord bot that adds an economy to a server along with an inventory system with guild item shops.

## Features

  * Economy
    - Independent economies between servers.
    - Customizable currency, allowing the use of emojis or any currency desired.
  * Items
    - An item consists of a few fields
        - ```name``` - The name of the item
        - ```description``` - The description for the item ***optional***
        - ```value``` - The cost to purchase item **_Required_**
        - ```image url``` - A url to an image to display when
        - ```amount``` - The amount of an item *(defaults to 1)*
    - Inventory system for each user per server.
    - Guild Item shop where admins can add custom items.
    - Can configure settings for your server to limit inventory sizes.
  * Database
    - Utilizes PostgreSQL for storing data on servers and users.
#### Item Example
![alt text](https://i.imgur.com/QhRvk6a.png "Item example in Discord")  

## Commands
Slash commands available for use with the bot
### Economy
  * ```/balance``` - Check the users balance within the guild
  * ```/balancetop``` - Check the top ten users within the guild
  * ```/addmoney [amount] [user]``` - Add money to a users balance ***Requires Admin Permission***
  * ```/removemoney [amount] [user]``` - Remove money from a users balance ***Requires Admin Permission***
  * ```/setbalance [amount] [user]``` - Set the balance of a user ***Requires Admin Permission***
  * ```/setcurrency [currency]``` - Set the currency for the guild ***Requires Admin Permission***

### Item Shop
  * ```/shop``` - Opens the item shop where you can purchase items
  * ```/shopeditor subcommand``` - Allows admins to edit the item shop
      - ```/shopeditor editor``` - Opens the shop editor tool for editing items currently available within the item shop or remove an item
      - ```/shopeditor add [name] [description] [value] [image url]``` - Add an item to the item shop
### Inventory
  * ```/inventory [user]``` - Allows a user to check another users inventory or their own if no user is given as input
  * ```/additem [user] [item]``` - Allows an admin to give an item to a user from a given list of items available within the server
  * ```/removeitem [user] [item]``` - Allows an admin to remove an item from a users inventory
  * ```/clearinventory [user]``` - Clears a given users inventory of all items
  * ```/maxinventory [amount]``` - Allows admins to set the max inventory size for a guild *(defaults to no limit)*

## TODO

### Bot Features
#### Commands
- [x] Blackjack and Rock, Paper, Scissors
  - Games so that users can make money
- [ ] More Games
  - [ ] Poker
  - [ ] Pet Battles
    - Purchase and train pets to fight different tiers of enemies
    - Death results in lose of pet
    - Higher level pet can fight higher level creatures with less chance to die, with greater rewards
- [ ] Refine work command
  - Command cooldown
  - Upgrades to generate more revenue
    - Item that increaases chance to generate more money
- [ ] Add illicit work command
  - High risk high reward command
  - Chance to lose money instead of make money
- [ ] Add trade command
#### Items
- [ ] Add ability to create items
- [ ] Item effects
  - Certain items can be given effects that can contribute to bonuses for commands, or have trade value
- [ ] Pets
  - [ ] Pet training
  - [ ] Pet combat
  - [ ] Pet skills

#### Website
- [ ] Add Bot website
  - A place to add bot to Discord servers
  - Along with a dashboard for editing guild settings
- [ ] Premium upgrade for guilds
  - [ ] Personal guild page
  - [ ] Shop page for users to interact with and purchase items
  - [ ] Visualizer for user inventories for crafting, trading, etc.
