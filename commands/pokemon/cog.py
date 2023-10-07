from discord.ext import commands

import discordbot


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot


async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
