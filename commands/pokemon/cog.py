from discord import Member, User, app_commands, Interaction
from discord.ext import commands
from typing import List
from Views.Battles.WildBattleView import WildBattleView
from Views.DayCareView import DayCareAddView, DayCareView
from Views.GiveCandyView import GiveCandyView
from Views.PokedexView import PokedexView
from Views.UsePotionView import UsePotionView
from commands.autofills.autofills import autofill_boxpkmn, autofill_nonteam, autofill_owned, autofill_pokemon
from commands.views.Pagination.DaycareView import DaycareView
from commands.views.Pagination.PokemonSearchView import PokemonSearchView
from commands.views.Selection.DaycareAddView import DaycareAddView
from commands.views.Selection.NicknameView import NicknameView
import discordbot

from Views.EvolveView import EvolveView
from globals import PokemonColor, botImage
from middleware.decorators import command_lock, elitefour_check, method_logger, trainer_check
from services import commandlockservice, gymservice, itemservice, pokemonservice, statservice, trainerservice, typeservice
from middleware.decorators import method_logger, trainer_check
from services.utility import discordservice, discordservice_permission, discordservice_pokemon


class PokemonCommands(commands.Cog, name="PokemonCommands"):

  discordBot = discordbot.GetBot()

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    

  #region Pokemon
    
  @app_commands.command(name="spawn",
                        description="Spawn an Pokemon to capture or fight.")
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def spawn(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pokemon,ditto = pokemonservice.SpawnPokemon(trainer.Region,
      max([b for b in trainer.Badges if b < 1000]) if len(trainer.Badges) > 0 else 0,
      #Voltage Reward
      trainerservice.GetShinyOdds(trainer)
    )
    trainerservice.EggInteraction(trainer)
    if not pokemon:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      await discordservice_pokemon.PrintSpawnResponse(inter, 0, [])
    await WildBattleView(trainer, pokemon, ditto).send(inter)

  @app_commands.command(name="spawnlegendary",
                        description="Spawn a Legendary Pokemon to capture or fight.")
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def spawnlegendary(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    for b in gymservice.GetBadgesByRegion(trainer.Region):
      if b not in trainer.Badges:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_pokemon.PrintSpawnLegendaryResponse(inter, 0, [])
    if trainer.Region not in trainer.EliteFour and [p for p in trainer.OwnedPokemon if p.Pokemon_Id in [po.Id for po in pokemonservice.GetLegendaryInRegion(trainer.Region)]]:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintSpawnLegendaryResponse(inter, 1, [])
    pokemon = pokemonservice.SpawnLegendary(trainer.Region, trainerservice.GetShinyOdds(trainer), [p.Pokemon_Id for p in trainer.OwnedPokemon])
    if not pokemon:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintSpawnLegendaryResponse(inter, 2, [])
    await WildBattleView(trainer, pokemon).send(inter)

  @app_commands.command(name="pokecenter",
                        description="Heal all HP and Ailments from Pokemon on your team.")
  @method_logger(False)
  @trainer_check
  @elitefour_check
  @command_lock
  async def pokecenter(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    for p in trainerservice.GetTeam(trainer):
      pokemonservice.HealPokemon(p, pokemonservice.GetPokemonById(p.Pokemon_Id))
    trainerservice.UpsertTrainer(trainer)
    commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
    return await discordservice.SendEmbed(inter, discordservice.CreateEmbed(
      'Healed', 
      'All Pokemon in your party have been healed to full HP and cured of any ailments.', 
      PokemonColor,
      thumbnail=botImage))

  @app_commands.command(name="usepotion",
                        description="Use a healing item on one of your party Pokemon.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def usepotion(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not itemservice.GetTrainerPotions(trainer):
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_pokemon.PrintUsePotionResponse(inter, 0, [])
    return await UsePotionView(trainer).send(inter)

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
      searchList = statservice.GetAllTypes()
      searchList.sort(key=lambda x: x.Name)
      for type in searchList:
        if current.lower() in type.Name.lower():
            choiceList.append(app_commands.Choice(name=type.Name, value=str(type.Id)))
            if len(choiceList) == 25:
              break
    return choiceList

  @app_commands.command(name="pokelist",
                        description="Gives a list of Pokemon belonging to a category.")
  @app_commands.choices(search=[
      app_commands.Choice(name="Color", value="color"),
      app_commands.Choice(name="Type", value="type")
  ])
  @app_commands.autocomplete(filter=filter_autocomplete)
  @method_logger(False)
  async def pokelist(self, inter: Interaction, search: app_commands.Choice[str], filter: str):
    if search.value == 'color':
      pokemonList = pokemonservice.GetPokemonByColor(filter)
      if not pokemonList:
        return await discordservice_pokemon.PrintPokeInfoResponse(inter, 1, [filter])
      pokemonList.sort(key=lambda x: x.Name)
      dexViewer = PokemonSearchView(inter, pokemonList, f"List of {filter} Pokemon")
      await dexViewer.send()
    elif search.value == 'type':
      pokemonList = pokemonservice.GetPokemonByType(filter)
      if not pokemonList:
        return await discordservice_pokemon.PrintPokeInfoResponse(inter, 2, [statservice.GetType(int(filter)).Name])
      dexViewer = PokemonSearchView(inter, pokemonList, f"List of {filter} type Pokemon")
      await dexViewer.send()
    else:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 3, [])
    
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
  async def pokedex(self, inter: Interaction, user: Member|None = None, dex: int|None = None, pokemon: int|None = None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if not pokemon:
      data = pokemonservice.GetAllPokemon()
      data.sort(key=lambda x: x.PokedexId)
      dexViewer = PokedexView(user if user else inter.user,trainer,dex,False,data)
    else:
      data = pokemonservice.GetPokemonById(pokemon)
      dataList = [data for d in [data.Sprite, data.ShinySprite, data.SpriteFemale, data.ShinySpriteFemale] if d]
      dexViewer = PokedexView(user if user else inter.user,trainer,dex,True,dataList+[data])
    await dexViewer.send(inter)

  @app_commands.command(name="nickname",
                        description="Nickname one of your Pokemon.")
  @app_commands.autocomplete(pokemon=autofill_owned)
  @method_logger(True)
  @trainer_check
  @command_lock
  async def nickname(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
    await NicknameView(trainer, pkmnList).send(inter)

  #endregion


  #region Evolution

  @app_commands.command(name="evolve",
                        description="Evolve one of your party Pokemon.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def evolve(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pokeList = pokemonservice.GetPokemonThatCanEvolve(trainer)
    if not pokeList:
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_pokemon.PrintEvolveResponse(inter, 0, [])
    return await EvolveView(trainer, pokeList).send(inter)

  @app_commands.command(name="givecandy",
                        description="Give a candy to a Pokemon.")
  @method_logger(True)
  @trainer_check
  @command_lock
  async def givecandy(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not itemservice.GetTrainerCandy(trainer):
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 0, [])
    if not [p for p in trainerservice.GetTeam(trainer) if p.Level < 100]:
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_pokemon.PrintGiveCandyResponse(inter, 1, [])
    return await GiveCandyView(trainer).send(inter)


  @app_commands.command(name="daycare",
                        description="Add to or check on the daycare.")
  @app_commands.autocomplete(pokemon=autofill_boxpkmn)
  @method_logger(True)
  @trainer_check
  @elitefour_check
  async def daycare(self, inter: Interaction, user: Member|None = None, pokemon: int|None = None):
    if not user or user.id == inter.user.id:
      if commandlockservice.IsLocked(inter.guild.id, inter.user.id):
        return await discordservice_permission.SendError(inter, 'commandlock')
      commandlockservice.AddLock(inter.guild.id, inter.user.id)

    #Viewing Daycare
    if not pokemon:
      trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
      if len(trainer.Daycare) == 0:
        return await discordservice_pokemon.PrintDaycareResponse(inter, 0 if user else 1, [user.display_name] if user else [])
      else:
        return await DayCareView(user if user else inter.user, trainer, (user.id == inter.user.id) if user else True).send(inter)
      
    #Adding To Daycare
    else:
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      if len(trainer.Daycare) >= 2:
        return await discordservice_pokemon.PrintDaycareResponse(inter, 2, [])
      else:
        pokeList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
        if not pokeList:
          pkmn = pokemonservice.GetPokemonById(pokemon)
          return await discordservice_pokemon.PrintDaycareResponse(inter, 3, [pkmn.Name] if pkmn else ['N/A'])
        return await DayCareAddView(trainer, pokeList).send(inter)

  #endregion

async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
