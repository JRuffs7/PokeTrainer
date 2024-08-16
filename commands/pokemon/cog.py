from discord import Member, app_commands, Interaction
from discord.ext import commands
from typing import List
from commands.autofills.autofills import autofill_nonteam, autofill_owned, autofill_pokemon, autofill_pokemon_legendary_spawn, autofill_special
from commands.views.PokeShopView import PokeShopView
from commands.views.BattleSimView import BattleSimView
from commands.views.Pagination.DaycareView import DaycareView
from commands.views.Pagination.DexView import DexView
from commands.views.Pagination.PokemonSearchView import PokemonSearchView
from commands.views.Pagination.WishlistView import WishlistView
from commands.views.Selection.CandyView import CandyView
from commands.views.Selection.DaycareAddView import DaycareAddView
from commands.views.Selection.HatchView import HatchView
from commands.views.Selection.NicknameView import NicknameView
from commands.views.SpawnPokemonView import SpawnPokemonView
import discordbot

from commands.views.Selection.EvolveView import EvolveView
from globals import AdminList
from middleware.decorators import command_lock, method_logger, trainer_check
from services import pokemonservice, typeservice, trainerservice, zoneservice
from services.utility import discordservice_pokemon


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  #region Spawn
    
  @app_commands.command(name="spawn",
                        description="Spawn an Pokemon to capture or fight.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def spawn(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if inter.user.id in AdminList or trainerservice.CanCallSpawn(trainer):
      pokemon = pokemonservice.SpawnPokemon(
        None if trainer.CurrentZone == 0 else zoneservice.GetZone(trainer.CurrentZone),
        max([b for b in trainer.Badges if b < 1000]) if len(trainer.Badges) > 0 else 0,
        #Voltage Reward
        trainerservice.GetShinyOdds(trainer)
      )
      trainerservice.EggInteraction(trainer)
      await SpawnPokemonView(inter, trainer, pokemon).send()
    else:
      return await discordservice_pokemon.PrintSpawnResponse(inter, 0, [trainer.LastSpawnTime])

  @app_commands.command(name="hatch",
                        description="Hatch one or more of your eggs.")
  @method_logger(True)
  @trainer_check
  async def hatch(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    hatchable = [e for e in trainer.Eggs if trainerservice.CanEggHatch(e)]
    if hatchable:
      await HatchView(inter, trainer, hatchable).send()
    else:
      return await discordservice_pokemon.PrintHatchResponse(inter, 0 if trainer.Eggs else 1)

  @app_commands.command(name="wishlist",
                        description="Add to or view your special spawn wishlist.")
  @app_commands.autocomplete(pokemon=autofill_special)
  @method_logger(True)
  @trainer_check
  async def wishlist(self, inter: Interaction, pokemon: int = None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)

    #Viewing Wishlist
    if not pokemon:
      if len(trainer.Wishlist) == 0:
        return await discordservice_pokemon.PrintWishlistResponse(inter, 1, [])
      return await WishlistView(inter, trainer).send()
    
    #Adding To Wishlist
    if len(trainer.Wishlist) >= 5:
      return await discordservice_pokemon.PrintWishlistResponse(inter, 2, [])
    
    pkmn = pokemonservice.GetPokemonById(pokemon)
    if not pkmn or not pokemonservice.IsSpecialSpawn(pkmn):
      return await discordservice_pokemon.PrintWishlistResponse(inter, 4, pkmn.Name if pkmn else 'N/A')

    return await discordservice_pokemon.PrintWishlistResponse(
      inter, 
      0 if trainerservice.TryAddWishlist(trainer, pokemon) else 3,
      pokemonservice.GetPokemonById(pokemon).Name
    )

  @app_commands.command(name="pokeshop",
                        description="Buy a specific Pokemon in exchange for Money or Pokeballs.")
  @app_commands.autocomplete(pokemon=autofill_pokemon_legendary_spawn)
  @method_logger(True)
  @trainer_check
  async def pokeshop(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer.Money <= 0:
      return await discordservice_pokemon.PrintPokeShopResponse(inter, 0)
    pkmn = pokemonservice.GetPokemonById(pokemon)
    if not pkmn:
      return await discordservice_pokemon.PrintPokeShopResponse(inter, 1)
    if not pokemonservice.IsLegendaryPokemon(pkmn) or pokemonservice.GetPreviousStages(pkmn):
      return await discordservice_pokemon.PrintPokeShopResponse(inter, 2, pkmn.Name)
    if trainer.Money < pokemonservice.GetShopValue(pkmn):
      return await discordservice_pokemon.PrintPokeShopResponse(inter, 3, pkmn.Name)
    if "4" not in trainer.Pokeballs or trainer.Pokeballs["4"] < 20:
      return await discordservice_pokemon.PrintPokeShopResponse(inter, 4, pkmn.Name)
    spawn = pokemonservice.GenerateSpawnPokemon(pkmn, level=1)
    spawn.IsShiny = (spawn.IsShiny and trainer.Money >= pokemonservice.GetShopValue(pkmn)*2 and trainer.Pokeballs["4"] >= 30)

    return await PokeShopView(inter, trainer, spawn).send()

  #endregion


  #region PokeInfo

  async def filter_autocomplete(self, inter: Interaction, current: str) -> List[app_commands.Choice[str]]:
    search = inter.namespace['search']
    choiceList = []
    if search == 'color':
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
      app_commands.Choice(name="Color", value="color"),
      app_commands.Choice(name="Type", value="type")
  ])
  @app_commands.autocomplete(filter=filter_autocomplete)
  @method_logger(True)
  async def pokeinfo(self, inter: Interaction, search: app_commands.Choice[str], filter: str):
    if search.value == 'color':
      await self.PokeInfoColor(inter, filter)
    elif search.value == 'type':
      await self.PokeInfoType(inter, filter)
    else:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 3, [])
    
  async def PokeInfoColor(self, inter: Interaction, color: str):
    pokemonList = pokemonservice.GetPokemonByColor(color)
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 1, [color])
    pokemonList.sort(key=lambda x: x.Name)
    dexViewer = PokemonSearchView(inter, pokemonList, f"List of {color} Pokemon")
    await dexViewer.send()

  async def PokeInfoType(self, inter: Interaction, type: str):
    pokemonList = pokemonservice.GetPokemonByType(type.lower())
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 2, [type])
    dexViewer = PokemonSearchView(inter, pokemonList, f"List of {type} type Pokemon")
    await dexViewer.send()


  @app_commands.command(name="pokedex",
                        description="Gives a list of full or singular Pokedex completion.")
  @app_commands.choices(dex=[
      app_commands.Choice(name="Pokedex", value=0),
      app_commands.Choice(name="Form Dex", value=1),
      app_commands.Choice(name="Shiny Dex", value=2)
  ])
  @app_commands.autocomplete(pokemon=autofill_pokemon)
  @method_logger(False)
  @trainer_check
  async def pokedex(self, inter: Interaction, user: Member|None, dex: int = None, pokemon: int = None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if not pokemon:
      dexType = "Pokedex" if not dex else "Form Dex" if dex == 1 else "Shiny Dex"
      data = pokemonservice.GetAllPokemon()
      data.sort(key=lambda x: x.PokedexId)
      trainerCompletion = f"{len(trainer.Pokedex) if not dex else len(trainer.Formdex) if dex == 1 else len(trainer.Shinydex)}/{len(set(p.PokedexId for p in data)) if not dex else len(data)}"
      dexViewer = DexView(
        inter, 
        user if user else inter.user,
        trainer,
        dex,
        20, 
        data,
        f"{user.display_name if user else inter.user.display_name}'s {dexType} ({trainerCompletion})")
    else:
      dexType = "Pokedex" if dex and dex == 0 else "Form Dex"
      data = pokemonservice.GetPokemonById(pokemon)
      dexViewer = DexView(
        inter, 
        user if user else inter.user,
        trainer,
        dex if dex and dex <= 1 else 1,
        1, 
        [data, data],
        f"{user.display_name if user else inter.user.display_name}'s {data.Name} {dexType}")
    await dexViewer.send()


  @app_commands.command(name="battlesim",
                        description="Simulates a wild/gym battle between two Pokemon.")
  @app_commands.choices(battle=[
      app_commands.Choice(name="Gym Battle", value=0),
      app_commands.Choice(name="Wild Battle", value=1)
  ])
  @app_commands.autocomplete(attacker=autofill_pokemon)
  @app_commands.autocomplete(defender=autofill_pokemon)
  @method_logger(True)
  async def battlesim(self, inter: Interaction, battle: int, attacker: int, defender: int):
    attackMon = pokemonservice.GetPokemonById(attacker)
    defendMon = pokemonservice.GetPokemonById(defender)
    if not attackMon or not defendMon:
      return await discordservice_pokemon.PrintBattleSimResponse(inter, 0, [])
    if not pokemonservice.CanSpawn(defendMon) and battle == 1:
      return await discordservice_pokemon.PrintBattleSimResponse(inter, 1, [defendMon.Name])
    await BattleSimView(inter, attackMon, defendMon, battle == 0).send()


  @app_commands.command(name="nickname",
                        description="Nickname one of your Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_owned)
  @method_logger(True)
  @trainer_check
  async def nickname(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
    await NicknameView(inter, trainer, pkmnList).send()

  #endregion


  #region Evolution

  async def autofill_evolve(self, inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    evList = pokemonservice.GetPokemonThatCanEvolve(trainer, [p for p in trainer.OwnedPokemon])
    pkmnList = pokemonservice.GetPokemonByIdList([e.Pokemon_Id for e in evList])
    pkmnList.sort(key=lambda x: x.Name)
    for pkmn in pkmnList:
      if current.lower() in pkmn.Name.lower():
        data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
      if len(data) == 25:
        break
    return data

  @app_commands.command(name="evolve",
                        description="Evolve your Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_evolve)
  @method_logger(True)
  @trainer_check
  async def evolve(self, inter: Interaction, pokemon: int | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pokeList = pokemonservice.GetPokemonThatCanEvolve(trainer, [p for p in trainer.OwnedPokemon if (p.Pokemon_Id == pokemon if pokemon else True)])
    if not pokeList:
      pkmn = pokemonservice.GetPokemonById(pokemon)
      return await discordservice_pokemon.PrintEvolveResponse(inter, 1 if pokemon else 0, pkmn.Name if pkmn else 'N/A')

    evolveView = EvolveView(inter, trainer, pokeList)
    return await evolveView.send()


  async def autofill_candy(self, inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Level < 100])
    pkmnList.sort(key=lambda x: x.Name)
    for pkmn in pkmnList:
      if current.lower() in pkmn.Name.lower():
        data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
      if len(data) == 25:
        break
    return data


  @app_commands.command(name="givecandy",
                        description="Give a candy to a Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_candy)
  @method_logger(True)
  @trainer_check
  async def givecandy(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pokeList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon and p.Level < 100]
    if not pokeList:
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 1, pokemonservice.GetPokemonById(pokemon).Name)
    candyList = [c for c in trainer.Candies if trainer.Candies[c] > 0]
    if not candyList: 
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 0)

    candyView = CandyView(inter, trainer, pokeList)
    return await candyView.send()


  @app_commands.command(name="daycare",
                        description="Add to or check on your daycare.")
  @app_commands.autocomplete(pokemon=autofill_nonteam)
  @method_logger(True)
  @trainer_check
  async def daycare(self, inter: Interaction, pokemon: int|None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)

    #Viewing Daycare
    if not pokemon:
      if len(trainer.Daycare) == 0:
        return await discordservice_pokemon.PrintDaycareResponse(inter, 0, [])
      return await DaycareView(inter, trainer).send()
    
    #Adding To Daycare
    #Kalos Reward
    if len(trainer.Daycare) >= (4 if trainerservice.HasRegionReward(trainer, 6) else 2):
      return await discordservice_pokemon.PrintDaycareResponse(inter, 1, [])
    
    pokeList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
    if not pokeList:
      return await discordservice_pokemon.PrintDaycareResponse(inter, 2, [pokemonservice.GetPokemonById(pokemon).Name])

    return await DaycareAddView(inter, trainer, pokeList).send()

  #endregion

async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
