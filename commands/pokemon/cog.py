from discord import app_commands
from discord.ext import commands
from typing import List
import discord
import discordbot

from commands.views.PokedexView import PokedexView
from globals import PokemonColor
from services import pokemonservice, typeservice
from services.utility import discordservice


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  async def filter_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    search = int(inter.namespace['search'])
    choiceList = []
    if search == 'single':
      searchList = pokemonservice.GetAllPokemon()
      searchList.sort(key=lambda x: x.Name)
      for pkmn in searchList:
        if current.lower() in pkmn.Name.lower():
          choiceList.append(app_commands.Choice(name=pkmn.Name, value=f"{pkmn.Id}"))
          if len(choiceList) == 25:
            break
    elif search == 'color':
      searchList = pokemonservice.GetPokemonColors()
      searchList.sort()
      for color in searchList:
        if current.lower() in color.lower():
          choiceList.append(app_commands.Choice(name=color, value=color))
          if len(choiceList) == 25:
            break
    elif search == 'type':
      searchList = typeservice.GetAllTypes()
      for type in searchList:
        if current.lower() in type.Name.lower():
            choiceList.append(app_commands.Choice(name=type.Name, value=type.Name))
            if len(choiceList) == 25:
              break
    return choiceList


  @app_commands.command(name="pokeinfo",
                        description="Lists all Pokemon for the given color alphabetically.")
  @app_commands.choices(search=[
      discord.app_commands.Choice(name="Single Pokemon", value='single'),
      discord.app_commands.Choice(name="Color", value="color"),
      discord.app_commands.Choice(name="Type", value="type")
  ])
  @app_commands.autocomplete(filter=filter_autocomplete)
  async def pokeinfo(self,
                      inter: discord.Interaction,
                      search: app_commands.Choice[str] | None,
                      filter: str):
    print("POKEMON INFO called")

    


async def PokeInfoSingle(inter, pokemonId):
  pokemonList = pokemonservice.SplitPokemonForSearch(pokemonservice.GetPokemonById(pokemonId))
  if not pokemonList:
    return await discordservice.SendErrorMessage(inter, 'pokeinfo')
  dexViewer = PokedexView(inter, 1, None, 'Pokemon Search')
  dexViewer.data = pokemonList
  await dexViewer.send()
  

async def PokeInfoColor(inter, color):
  pokemonList = pokemonservice.GetPokemonByColor(color.lower())
  if not pokemonList:
    return await discordservice.SendErrorMessage(inter, 'pokeinfo')
  pokemonList.sort(key=lambda x: x.Name)
  dexViewer = PokedexView(inter, 10, None, f"List of {color} Pokemon")
  dexViewer.data = pokemonList
  await dexViewer.send()


async def PokeInfoType(inter, type):
  pokemonList = pokemonservice.GetPokemonByType(type.lower())
  if not pokemonList:
    return await discordservice.SendErrorMessage(inter, 'pokeinfo')
  dexViewer = PokedexView(inter, 10, None, f"List of {type} type Pokemon")
  dexViewer.data = pokemonList
  await dexViewer.send()


async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
