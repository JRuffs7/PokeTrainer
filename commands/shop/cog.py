from discord import app_commands
from discord.ext import commands
from discord.user import discord

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
    return await discordservice.SendEmbed(inter, embed)

  @app_commands.command(
      name="buypokeball",
      description="Buy one or multiple of the selected Pokeball")
  @app_commands.choices(ball=[
      discord.app_commands.Choice(name="Pokeball", value=1),
      discord.app_commands.Choice(name="Greatball", value=2),
      discord.app_commands.Choice(name="Ultraball", value=3)
  ])
  async def buypokeball(self, inter: discord.Interaction,
                        ball: app_commands.Choice[int], amount: int | None):
    print(f"BUY POKEBALL called")
    try:
      sale = trainerservice.TryBuyPokeball(inter.guild_id, inter.user.id,
                                           ball.value, amount or 1)
      if sale is None:
        return await discordservice.SendErrorMessage(inter, 'buypokeball')

      if sale and sale[0]:
        return await discordservice.SendMessage(
            inter, "Purchase Success",
            f"{ball.name} x{amount or 1} purchased for ${sale[1]}",
            ShopSuccessColor, True)
      return await discordservice.SendMessage(
          inter, "Purchase Failed",
          f"{ball.name} x{amount or 1} could not be purchased due to insufficient funds.\nPlease check the shop list by using **/shop** and your current funds by using **/trainerinfo** or **/inventory**",
          ShopFailColor, True)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)

  @app_commands.command(
      name="sellpokeball",
      description="Sell one or multiple of the selected Pokeball")
  @app_commands.choices(ball=[
      discord.app_commands.Choice(name="Pokeball", value=1),
      discord.app_commands.Choice(name="Greatball", value=2),
      discord.app_commands.Choice(name="Ultraball", value=3)
  ])
  async def sellpokeball(self, inter: discord.Interaction,
                         ball: app_commands.Choice[int], amount: int | None):
    print(f"SELL POKEBALL called")
    try:
      sale = trainerservice.TrySellPokeball(inter.guild_id, inter.user.id,
                                            ball.value, amount or 1)

      if sale[0] > 0:
        return await discordservice.SendMessage(
            inter, "Sell Success",
            f"{ball.name} x{sale[0]} sold for ${sale[1]}", ShopSuccessColor,
            True)
      return await discordservice.SendMessage(
          inter, "Sell Failed",
          f"You do not own any {ball.name}s.\nPlease check your inventory by using **/inventory**",
          ShopFailColor, True)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)

  @app_commands.command(
      name="buypotion",
      description="Buy one or multiple of the selected Potion")
  @app_commands.choices(potion=[
      discord.app_commands.Choice(name="Potion", value=1),
      discord.app_commands.Choice(name="Super Potion", value=2),
      discord.app_commands.Choice(name="Hyper Potion", value=3),
      discord.app_commands.Choice(name="Max Potion", value=4)
  ])
  async def buypotion(self, inter: discord.Interaction,
                      potion: app_commands.Choice[int], amount: int | None):
    print(f"BUY POKEBALL called")
    try:
      sale = trainerservice.TryBuyPotion(inter.guild_id, inter.user.id,
                                         potion.value, amount or 1)
      if sale is None:
        return await discordservice.SendErrorMessage(inter, 'buypotion')

      if sale[0]:
        return await discordservice.SendMessage(
            inter, "Purchase Success",
            f"{potion.name} x{amount or 1} purchased for ${sale[1]}",
            ShopSuccessColor, True)
      return await discordservice.SendMessage(
          inter, "Purchase Failed",
          f"{potion.name} x{amount or 1} could not be purchased due to insufficient funds.\nPlease check the shop list by using **/shop** and your current funds by using **/trainerinfo** or **/inventory**",
          ShopFailColor, True)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)

  @app_commands.command(
      name="sellpotion",
      description="Sell one or multiple of the selected Potion")
  @app_commands.choices(potion=[
      discord.app_commands.Choice(name="Potion", value=1),
      discord.app_commands.Choice(name="Super Potion", value=2),
      discord.app_commands.Choice(name="Hyper Potion", value=3),
      discord.app_commands.Choice(name="Max Potion", value=4)
  ])
  async def sellpotion(self, inter: discord.Interaction,
                       potion: app_commands.Choice[int], amount: int | None):
    print(f"SELL POKEBALL called")
    try:
      sale = trainerservice.TrySellPotion(inter.guild_id, inter.user.id,
                                          potion.value, amount or 1)

      if sale[0] > 0:
        return await discordservice.SendMessage(
            inter, "Sell Success",
            f"{potion.name} x{sale[0]} sold for ${sale[1]}", ShopSuccessColor,
            True)
      return await discordservice.SendMessage(
          inter, "Sell Failed",
          f"You do not own any {potion.name}s.\nPlease check your inventory by using **/inventory**",
          ShopFailColor, True)
    except TrainerInvalidException:
      return await discordservice.SendTrainerError(inter)


async def setup(bot: commands.Bot):
  await bot.add_cog(ShopCommands(bot))
