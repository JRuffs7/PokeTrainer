from discord import app_commands
from discord.ext import commands
from typing import List
import discord
import discordbot

from commands.views.PokedexView import PokedexView
from globals import PokemonColor
from services import pokemonservice
from services.utility import discordservice


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  async def color_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name=c,value=c) for c in pokemonservice.GetPokemonColors() if current.lower() in c.lower()]


  @app_commands.command(name="pokemoncolors",
                        description="Lists all Pokemon for the given color alphabetically.")
  @app_commands.choices(images=[
      discord.app_commands.Choice(name="Yes", value=1),
      discord.app_commands.Choice(name="No", value=0)
  ])
  @app_commands.autocomplete(color=color_autocomplete)
  async def PokemonColors(self,
                        inter: discord.Interaction,
                        color: str,
                        images: app_commands.Choice[int] | None):
    print("POKEMON COLORS called")
    pokemonList = pokemonservice.GetPokemonByColor(color)
    if pokemonList:
      pokemonList.sort(key=lambda x: x.Name)
      if images and images.value:
        dexViewer = PokedexView(inter, 1, None, f"List of {color} Pokemon")
      else:
        dexViewer = PokedexView(inter, 10, None, f"List of {color} Pokemon")
      dexViewer.data = pokemonList
      await dexViewer.send()
    await discordservice.SendMessage(inter, f"List of {color} Pokemon", "No Pokemon fit this color", PokemonColor, True)


async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
