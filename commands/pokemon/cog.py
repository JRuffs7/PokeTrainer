from discord import app_commands, Interaction
from discord.ext import commands
from typing import List
from commands.views.Pagination.PokemonSearchView import PokemonSearchView
from commands.views.Selection.CandyView import CandyView
from commands.views.Selection.HatchView import HatchView
from commands.views.SpawnPokemonView import SpawnPokemonView
import discordbot

from commands.views.Selection.EvolveView import EvolveView
from globals import AdminList
from middleware.decorators import method_logger, trainer_check
from services import pokemonservice, typeservice, trainerservice
from services.utility import discordservice_pokemon


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  #region Spawn
    
  @app_commands.command(name="spawn",
                        description="Spawn an Pokemon to capture or fight.")
  @method_logger
  @trainer_check
  async def spawn(self, inter: Interaction):
    pokemon = pokemonservice.SpawnPokemon()
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    trainerservice.EggInteraction(trainer)
    if inter.user.id in AdminList or trainerservice.CanCallSpawn(trainer):
      await SpawnPokemonView(inter, trainer, pokemon).send()
    else:
      return await discordservice_pokemon.PrintSpawnResponse(inter, 0, [trainer.LastSpawnTime])

  @app_commands.command(name="hatch",
                        description="Hatch one or more of your eggs.")
  @method_logger
  @trainer_check
  async def hatch(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    hatchable = [e for e in trainer.Eggs if trainerservice.CanEggHatch(e)]
    if hatchable:
      await HatchView(inter, trainer, hatchable).send()
    else:
      return await discordservice_pokemon.PrintHatchResponse(inter, 0 if trainer.Eggs else 1)

  #endregion


  #region PokeInfo

  async def filter_autocomplete(self, inter: Interaction, current: str) -> List[app_commands.Choice[str]]:
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

  @app_commands.command(name="pokeinfo",
                        description="Gives information for a single, or list, of Pokemon.")
  @app_commands.choices(search=[
      app_commands.Choice(name="Single Pokemon", value='single'),
      app_commands.Choice(name="Color", value="color"),
      app_commands.Choice(name="Type", value="type")
  ])
  @app_commands.autocomplete(filter=filter_autocomplete)
  @method_logger
  async def pokeinfo(self,
                      inter: Interaction,
                      search: app_commands.Choice[str],
                      filter: str):
    if search.value == 'single' and filter.isnumeric():
      await self.PokeInfoSingle(inter, int(filter))
    elif search.value == 'color':
      await self.PokeInfoColor(inter, filter)
    elif search.value == 'type':
      await self.PokeInfoType(inter, filter)
    else:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 3, [])
    

  async def PokeInfoSingle(self, inter: Interaction, pokemonId: int):
    pokemonList = pokemonservice.GeneratePokemonSearchGroup(pokemonId)
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 0, [])
    dexViewer = PokemonSearchView(inter, 1, pokemonList, 'Pokemon Search')
    dexViewer.data = pokemonList
    await dexViewer.send()
    

  async def PokeInfoColor(self, inter: Interaction, color: str):
    pokemonList = pokemonservice.GetPokemonByColor(color)
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 1, [color])
    pokemonList.sort(key=lambda x: x.Name)
    dexViewer = PokemonSearchView(inter, 10, pokemonList, f"List of {color} Pokemon")
    await dexViewer.send()


  async def PokeInfoType(self, inter: Interaction, type: str):
    pokemonList = pokemonservice.GetPokemonByType(type.lower())
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 2, [type])
    dexViewer = PokemonSearchView(inter, 10, pokemonList, f"List of {type} type Pokemon")
    await dexViewer.send()

  #endregion


  #region Evolution

  async def autofill_evolution(self, inter: Interaction, current):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      pokeList = [p for p in trainer.OwnedPokemon if pokemonservice.CanTrainerPokemonEvolve(p)]
      for pkmn in pokeList:
        displayname = pokemonservice.GetPokemonDisplayName(pkmn)
        if current.lower() in displayname.lower():
          data.append(app_commands.Choice(name=displayname, value=pkmn.Id))
        if len(data) == 25:
          break
    return data

  @app_commands.command(name="evolve",
                        description="Evolve your Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_evolution)
  @method_logger
  @trainer_check
  async def evolve(self, inter: Interaction, pokemon: str | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pokeList = [p for p in trainer.OwnedPokemon if pokemonservice.CanTrainerPokemonEvolve(p)]
    if pokemon:
      pokeList = [p for p in pokeList if p.Id == pokemon]

    if not pokeList:
      return await discordservice_pokemon.PrintEvolveResponse(inter, 0)

    evolveView = EvolveView(inter, trainer, pokeList)
    return await evolveView.send()

  async def autofill_givecandy(self, inter: Interaction, current: str):
    data: list[app_commands.Choice] = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      pokeList = [p for p in trainer.OwnedPokemon]
      for pkmn in pokeList:
        displayname = pokemonservice.GetPokemonDisplayName(pkmn, False, False)
        if current.lower() in displayname.lower() and displayname not in [d.name for d in data]:
          data.append(app_commands.Choice(name=displayname, value=displayname.lower()))
        if len(data) == 25:
          break
    return data

  @app_commands.command(name="givecandy",
                        description="Give a candy to a Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_givecandy)
  @method_logger
  @trainer_check
  async def givecandy(self, inter: Interaction, pokemon: str):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    candyList = [c for c in trainer.Candies if trainer.Candies[c] > 0]
    pokeList = [p for p in trainer.OwnedPokemon if pokemonservice.GetPokemonDisplayName(p, False, False).lower() == pokemon]
    if not candyList: 
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 0)
    if not pokeList:
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 1)

    candyView = CandyView(inter, trainer, pokeList)
    return await candyView.send()


  #endregion

async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
