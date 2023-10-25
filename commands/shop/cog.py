from discord import app_commands
from discord.ext import commands
from discord.user import discord
from typing import List

from globals import ShopFailColor, ShopSuccessColor
from models.CustomException import TrainerInvalidException
from services import itemservice, trainerservice
from services.utility import discordservice


class ShopCommands(commands.Cog, name="ShopCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="shop",
                        description="Prints all available items for sale")
  async def shop(self, inter: discord.Interaction):
    print("SHOP called")
    items = itemservice.GetFullShop()
    newline = '\n'
    pokeballString = f"__Pokeballs__\n{newline.join([f'{i.Name}: {i.BuyAmount}' for i in items[0]])}"
    potionString = f"__Potions__\n{newline.join([f'{i.Name}: {i.BuyAmount}' for i in items[1]])}"
    embed = discordservice.CreateEmbed(
        "PokeTrainer Shop",
        f"Use the **/buy*item*** commands to purchase.\n\n{pokeballString}\n\n{potionString}",
        ShopSuccessColor)
    return await discordservice.SendEmbed(inter, embed, True)

  async def item_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[int]]:
    pokeballs, potions = itemservice.GetFullShop()
    type = inter.namespace['type']
    choices = []
    if not type:
      choices.append(app_commands.Choice(name='Choose a type',value=0))
    else:
      for p in (pokeballs if type == "ball" else potions):
        if current.lower() in p.Name.lower():
          choices.append(app_commands.Choice(name=f"{p.Name} - ${p.BuyAmount if inter.command.name == 'buy' else p.SellAmount}",value=p.Id))
    return choices

  @app_commands.command(
      name="buy",
      description="Buy one or multiple of the selected item")
  @app_commands.choices(type=[
      discord.app_commands.Choice(name="Ball", value="ball"),
      discord.app_commands.Choice(name="Potion", value="potion")
  ])
  @app_commands.autocomplete(item=item_autocomplete)
  async def buy(self, inter: discord.Interaction,
                        type: app_commands.Choice[str], 
                        item: int, 
                        amount: int | None):
    print(f"BUY called")
    try:
      if type == "ball":
        sale = trainerservice.TryBuyPokeball(inter.guild_id, inter.user.id, item, amount or 1)
      else:
        sale = trainerservice.TryBuyPotion(inter.guild_id, inter.user.id, item, amount or 1)
        
      if sale is None:
        return await discordservice.SendMessage(
          inter, "Purchase Failed",
          f"Item could not be purchased.\nPlease check your current funds by using **/trainer** or **/inventory**",
          ShopFailColor)
      return await discordservice.SendMessage(
          inter, "Purchase Success",
          f"{sale.Name} x{amount or 1} purchased for ${(amount or 1)*sale.BuyAmount}",
          ShopSuccessColor)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)

  @app_commands.command(
      name="sell",
      description="Sell one or multiple of the selected item")
  @app_commands.choices(type=[
      discord.app_commands.Choice(name="Ball", value="ball"),
      discord.app_commands.Choice(name="Potion", value="potion")
  ])
  @app_commands.autocomplete(item=item_autocomplete)
  async def sell(self, inter: discord.Interaction,
                        type: app_commands.Choice[str], 
                        item: int, 
                        amount: int | None):
    print(f"SELL called")
    try:
      if type.value == "ball":
        sale = trainerservice.TrySellPokeball(inter.guild_id, inter.user.id, item, amount or 1)
      else:
        sale = trainerservice.TrySellPotion(inter.guild_id, inter.user.id, item, amount or 1)

      if not sale:
        return await discordservice.SendMessage(
          inter, "Sell Failed",
          f"You do not own any of the specified item.\nPlease check your inventory by using **/inventory**", ShopFailColor)
      return await discordservice.SendMessage(
          inter, "Sell Success",
          f"{sale['Item'].Name} x{sale['NumSold']} sold for ${sale['NumSold']*sale['Item'].SellAmount}", ShopSuccessColor)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)
    except Exception as e:
      print(f"{e}")


async def setup(bot: commands.Bot):
  await bot.add_cog(ShopCommands(bot))
