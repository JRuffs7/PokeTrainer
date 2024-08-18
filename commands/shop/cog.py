from discord import app_commands, Interaction
from discord.ext import commands
from commands.views.Selection.ShopView import ShopView
from commands.views.Selection.SpecialShopView import SpecialShopView
from middleware.decorators import command_lock, method_logger, trainer_check
from services import commandlockservice, trainerservice
from services.utility import discordservice_shop


class ShopCommands(commands.Cog, name="ShopCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="shop",
                        description="Buy or sell items.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def shop(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    shopViewer = ShopView(inter, trainer)
    await shopViewer.send()

  @app_commands.command(name="specialshop",
                        description="Special store for evolution items.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def specialshop(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    trainerservice.SpecialShopCheck(trainer)
    if not trainer.Shop.ItemIds:
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_shop.PrintSpecialShopResponse(inter)
    return await SpecialShopView(inter, trainer).send()

async def setup(bot: commands.Bot):
  await bot.add_cog(ShopCommands(bot))
