from discord import Member, app_commands, Interaction
from discord.ext import commands
from typing import List
from Views.Battles.WildBattleView import WildBattleView
from Views.DayCareView import DayCareAddView, DayCareView
from Views.GiveCandyView import GiveCandyView
from Views.LearnMovesView import LearnMovesView
from Views.LearnTMView import LearnTMView
from Views.PokedexView import PokedexView
from Views.UsePotionView import UsePotionView
from commands.autofills.autofills import autofill_boxpkmn, autofill_owned, autofill_pokemon, autofill_team, autofill_tms, autofill_types
from Views.PokemonSearchView import PokemonSearchView
from Views.NicknameView import NicknameView
import discordbot

from Views.EvolveView import EvolveView
from globals import PokemonColor, botImage
from middleware.decorators import command_lock, elitefour_check, method_logger, trainer_check
from services import commandlockservice, gymservice, itemservice, moveservice, pokemonservice, statservice, trainerservice, typeservice
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
      len([b for b in gymservice.GetBadgesByRegion(trainer.Region) if b.Id in trainer.Badges]),
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
    return await inter.followup.send(embed=discordservice.CreateEmbed(
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

  @app_commands.command(name="searchtypes",
                        description="Gives a list of Pokemon belonging to a chosen type.")
  @app_commands.autocomplete(type=autofill_types)
  @method_logger(True)
  async def searchtypes(self, inter: Interaction, type: int):
    pokemonList = pokemonservice.GetPokemonByType(type)
    if not pokemonList:
      return await discordservice_pokemon.PrintPokeInfoResponse(inter, 0, [statservice.GetType(type).Name])
    return await PokemonSearchView(pokemonList, type).send(inter)
    
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
  async def nickname(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
    await NicknameView(trainer, pkmnList).send(inter)


  @app_commands.command(name="learnmove",
                        description="Spend $500 to learn a move your Pokemon knows from leveling up.")
  @app_commands.autocomplete(pokemon=autofill_team)
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def learnmove(self, inter: Interaction, pokemon: str):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer.Money < 500:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintLearnMoveResponse(inter, 0, [])
    pkmn = next((p for p in trainer.OwnedPokemon if p.Id == pokemon),None) if pokemon in trainer.Team else None
    data = pokemonservice.GetPokemonById(pkmn.Pokemon_Id) if pkmn else None
    if not pkmn or not data:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintLearnMoveResponse(inter, 1, [])
    availableMoves = pokemonservice.GetAvailableLevelMoves(pkmn, data)
    if not availableMoves:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintLearnMoveResponse(inter, 2, [(pkmn.Nickname or data.Name)])
    await LearnMovesView(trainer, pkmn, data, availableMoves).send(inter)


  @app_commands.command(name="usetm",
                        description="Use a TM and teach a Pokemon a new move.")
  @app_commands.autocomplete(tm=autofill_tms)
  @method_logger(True)
  @trainer_check
  @command_lock
  async def usetm(self, inter: Interaction, tm: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if str(tm) not in trainer.TMs or trainer.TMs[str(tm)] <= 0:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintUseTMResponse(inter, 0, [])
    team = trainerservice.GetTeam(trainer)
    pkmnlist = [po for po in pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in team if tm not in p.LearnedMoves]) if tm in po.MachineMoves]
    if not pkmnlist:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintUseTMResponse(inter, 1, [])
    await LearnTMView(trainer, [t for t in team if t.Pokemon_Id in [po.Id for po in pkmnlist]], pkmnlist, tm).send(inter)

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
      targetuser = user if user else inter.user
      trainer = trainerservice.GetTrainer(inter.guild_id, targetuser.id)
      if len(trainer.Daycare) == 0:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_pokemon.PrintDaycareResponse(inter, 0 if user else 1, [targetuser.id] if user else [])
      return await DayCareView(user if user else inter.user, trainer, (user.id == inter.user.id) if user else True).send(inter)
      
    #Adding To Daycare
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if len(trainer.Daycare) >= 2:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_pokemon.PrintDaycareResponse(inter, 2, [])
    pokeList = [p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemon]
    if not pokeList:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      pkmn = pokemonservice.GetPokemonById(pokemon)
      return await discordservice_pokemon.PrintDaycareResponse(inter, 3, [pkmn.Name] if pkmn else ['N/A'])
    return await DayCareAddView(trainer, pokeList).send(inter)

  #endregion

async def setup(bot: commands.Bot):
  await bot.add_cog(PokemonCommands(bot))
