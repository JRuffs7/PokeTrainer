from discord import app_commands
from discord.ext import commands
from typing import List
import discord
import discordbot

from commands.views.PokedexView import PokedexView
from commands.views.EvolveView import EvolveView
from globals import PokemonColor
from services import pokemonservice, typeservice, trainerservice
from services.utility import discordservice


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  async def filter_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    search = inter.namespace['search']
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
      searchList = list(pokemonservice.GetPokemonColors())
      searchList.sort()
      for color in searchList:
        if current.lower() in color.lower():
          choiceList.append(app_commands.Choice(name=color, value=color))
          if len(choiceList) == 25:
            break
    elif search == 'type':
      searchList = typeservice.GetAllTypes()
      searchList.sort(key=lambda x: x.Name)
      for type in searchList:
        if current.lower() in type.Name.lower():
            choiceList.append(app_commands.Choice(name=type.Name, value=type.Name))
            if len(choiceList) == 25:
              break
    return choiceList

  #region PokeInfo

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
                      search: app_commands.Choice[str],
                      filter: str):
    print("POKEMON INFO called")
    if search.value == 'single':
      await self.PokeInfoSingle(inter, int(filter))
    elif search.value == 'color':
      await self.PokeInfoColor(inter, filter)
    elif search.value == 'type':
      await self.PokeInfoType(inter, filter)
    

  async def PokeInfoSingle(inter, pokemonId):
    pokemonList = pokemonservice.SplitPokemonForSearch(pokemonId)
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

  #endregion


  #region Evolution

  async def autofill_evolution(self, inter: discord.Interaction, current):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      pokeList = [p for p in trainer.OwnedPokemon if pokemonservice.CanTrainerPokemonEvolve(p)]
      for pkmn in pokeList:
        if current.lower() in pkmn.Name.lower():
          data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Name.lower()))
        if len(data) == 25:
          break
    return data

  @app_commands.command(name="evolve",
                        description="Evolve your Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_evolution)
  async def evolve(self, inter: discord.Interaction, pokemon: str | None):
    print("EVOLVE called")
    try:
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      if not trainer:
        return await discordservice.SendTrainerError(inter)
      
      pokeList = [p for p in trainer.OwnedPokemon if pokemonservice.CanTrainerPokemonEvolve(p)]
      if pokemon:
        pokeList = [p for p in pokeList if p.Name.lower() == pokemon]

      evolveView = EvolveView(inter, trainer, pokeList)
      await evolveView.send()
    except Exception as e:
      print(f"{e}")


  #endregion

async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
