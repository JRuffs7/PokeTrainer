from discord import app_commands, Interaction
from discord.ext import commands
from typing import List
from commands.views.Selection.ShopView import ShopView

from globals import ShopFailColor, ShopSuccessColor
from middleware.decorators import method_logger, trainer_check
from services import itemservice, trainerservice
from services.utility import discordservice


class ShopCommands(commands.Cog, name="ShopCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="shop",
                        description="Buy or sell items.")
  @method_logger
  @trainer_check
  async def shop(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    dexViewer = ShopView(inter, trainer)
    await dexViewer.send()

async def setup(bot: commands.Bot):
  await bot.add_cog(ShopCommands(bot))
