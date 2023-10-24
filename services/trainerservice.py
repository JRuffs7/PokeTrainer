from typing import List

from discord import Reaction

from dataaccess import trainerda
from globals import (
    to_dict,
    ErrorColor,
    FightReaction,
    GreatBallReaction,
    PokeballReaction,
)
from models.CustomException import TrainerInvalidException
from models.Trainer import Trainer
from models.Pokemon import PokedexEntry
from services import itemservice, pokemonservice, serverservice
from services.utility import discordservice


def GetTrainer(serverId, userId):
  return trainerda.GetTrainer(userId, serverId)

def UpsertTrainer(trainer):
  return trainerda.UpsertTrainer(trainer)

def DeleteTrainer(trainer):
  return trainerda.DeleteTrainer(trainer)

def StartTrainer(pokemonId, userId, serverId):
  pkmn = pokemonservice.GetPokemonById(pokemonId)
  if not pkmn:
    return None

  pokemon = pokemonservice.GenerateSpawnPokemon(pkmn)
  pokemon.Level = 5
  pokemon.EvolutionStage = 1

  trainer = Trainer({
      'UserId': userId,
      'ServerId': serverId,
      'Team': [pokemon.__dict__, None, None, None, None, None],
      'OwnedPokemon': [pokemon.__dict__],
      'Health': 50,
      'Money': 500,
      'PokeballList': [1,1,1,1,1]
  })
  UpsertTrainer(trainer)
  return (trainer, pkmn, pokemon)

#region Inventory/Items

def GetInventory(serverId, userId):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException

  pkblList = {
      "Pokeballs": trainer.PokeballList.count(1),
      "Greatballs": trainer.PokeballList.count(2),
      "Ultraballs": trainer.PokeballList.count(3),
      "Masterball": trainer.PokeballList.count(4),
  }
  ptnList = {
      "Potions": trainer.PotionList.count(1),
      "Super Potions": trainer.PotionList.count(2),
      "Hyper Potions": trainer.PotionList.count(3),
      "Max Potions": trainer.PotionList.count(4),
  }
  return (trainer.Money, dict(filter(lambda x: x[1] != 0, pkblList.items())),
          dict(filter(lambda x: x[1] != 0, ptnList.items())))

def TryBuyPokeball(serverId, userId, ballId, amount):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  ball = itemservice.GetPokeball(ballId)
  if not ball:
    return None

  if trainer.Money < (ball.BuyAmount * amount):
    return (False, 0)

  trainer.Money -= (ball.BuyAmount * amount)
  trainer.PokeballList = ModifyItemList(trainer.PokeballList, ballId, amount)
  trainerda.UpsertTrainer(trainer)
  return (True, (ball.BuyAmount * amount))

def TryBuyPotion(serverId, userId, potionId, amount):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  potion = itemservice.GetPotion(potionId)
  if not potion:
    return None

  if trainer.Money < (potion.BuyAmount * amount):
    return (False, 0)

  trainer.Money -= (potion.BuyAmount * amount)
  trainer.PotionList = ModifyItemList(trainer.PotionList, potionId, amount)
  trainerda.UpsertTrainer(trainer)
  return (True, (potion.BuyAmount * amount))

def TrySellPokeball(serverId, userId, ballId, amount):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  ball = itemservice.GetPokeball(ballId)
  if not ball:
    return (0, 0)

  currentNum = len(trainer.PokeballList)
  trainer.PokeballList = ModifyItemList(trainer.PokeballList, ballId,
                                        (0 - amount))
  postModNum = len(trainer.PokeballList)
  trainer.Money += (ball.SellAmount * (currentNum - postModNum))
  trainerda.UpsertTrainer(trainer)
  return (currentNum - postModNum,
          (ball.SellAmount * (currentNum - postModNum)))

def TrySellPotion(serverId, userId, potionId, amount):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  potion = itemservice.GetPotion(potionId)
  if not potion:
    return (0, 0)

  currentNum = len(trainer.PotionList)
  trainer.PotionList = ModifyItemList(trainer.PotionList, potionId,
                                      (0 - amount))
  postModNum = len(trainer.PotionList)
  trainer.Money += (potion.SellAmount * (currentNum - postModNum))
  trainerda.UpsertTrainer(trainer)
  return (currentNum - postModNum,
          (potion.SellAmount * (currentNum - postModNum)))

def TryUsePotion(serverId, userId, potionId):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  potion = itemservice.GetPotion(potionId)
  if not potion:
    return None

  if potionId not in trainer.PotionList:
    return (False, 0)

  if trainer.Health == 100:
    return (True, 0)

  preHealth = trainer.Health
  trainer.Health += potion.HealingAmount
  if trainer.Health > 100:
    trainer.Health = 100
  trainer.PotionList = ModifyItemList(trainer.PotionList, potionId, -1)
  trainerda.UpsertTrainer(trainer)
  return (True, (trainer.Health - preHealth))

def ModifyItemList(listProperty: List, itemId, amount):
  adding = amount > 0
  count = abs(amount)
  while count > 0:
    if adding:
      listProperty.append(itemId)
    elif itemId in listProperty:
      listProperty.remove(itemId)
    count -= 1
  return listProperty

#endregion

#region Pokedex

def GetPokedexList(serverId, userId, orderString, shiny):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  
  pokemonList = pokemonservice.ConvertSpawnPokemonToPokemon(trainer.OwnedPokemon)

  combine: List[PokedexEntry] = []
  for i, pkmn in enumerate(trainer.OwnedPokemon):
    if shiny != 2 or (shiny == 2 and pkmn.IsShiny):
      combine.append(PokedexEntry(
      {
        'Name': pokemonList[i].Name,
        'PokedexId': pokemonList[i].PokedexId,
        'Types': pokemonList[i].Types,
        'Sprite': pokemonList[i].GetImage(pkmn.IsShiny, pkmn.IsFemale),
        'Pokemon': to_dict(pkmn)
      }) )
  match orderString:
    case "height":
      if shiny == 3:
        combine.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Pokemon.Height))
      else:
        combine.sort(key=lambda x: x.Pokemon.Height)
    case "dex":
      if shiny == 3:
        combine.sort(key=lambda x: (-x.Pokemon.IsShiny,x.PokedexId))
      else:
        combine.sort(key=lambda x: x.PokedexId)
    case "name":
      if shiny == 3:
        combine.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Name))
      else:
        combine.sort(key=lambda x: x.Name)
    case "weight":
      if shiny == 3:
        combine.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Pokemon.Weight))
      else:
        combine.sort(key=lambda x: x.Pokemon.Weight)
    case _:
      if shiny == 3:
        combine.sort(key=lambda x: -x.Pokemon.IsShiny)
  return combine

def GetUniquePokemon(serverId, userId):
  trainer = GetTrainer(serverId, userId)
  uniqueIds = set()
  pokemonList = pokemonservice.ConvertSpawnPokemonToPokemon([p for p in trainer.OwnedPokemon if p.Pokemon_Id not in uniqueIds and not uniqueIds.add(p.Pokemon_Id)])
  return pokemonList

#endregion

#region Team

def GetTrainerTeam(serverId, userId):
  trainer = GetTrainer(serverId, userId)
  if not trainer:
    raise TrainerInvalidException
  
  team: List[PokedexEntry | None] = []
  for t in trainer.Team:
    if t:
      spawn = next((p for p in trainer.OwnedPokemon if p.Id == t), None)
      pkmn = pokemonservice.ConvertSpawnPokemonToPokemon([spawn])[0]
      team.append(PokedexEntry({
        'Name': pkmn.Name,
        'PokedexId': pkmn.PokedexId,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(spawn.IsShiny, spawn.IsFemale),
        'Pokemon': to_dict(spawn)
      }))
    else:
      team.append(None)
  return team

def SetTeamSlot(trainer, slotNum, pokemonId):
  trainer.Team[slotNum] = pokemonId
  UpsertTrainer(trainer)

#endregion

#region REACTION

async def ReationReceived(bot, user, reaction):
  try:
    message = reaction.message
    server = serverservice.GetServer(message.guild.id)
    users = [user async for user in reaction.users()]
    #Not a supported reaction
    if not users.__contains__(bot.user) or server is None:
      return False

    #Not a reaction on the last spawn pokemon or no spawn at all
    if reaction.message.id != server.LastSpawnMessage or not server.LastSpawned:
      return False

    spawn = server.LastSpawned
    trainer = GetTrainer(server.ServerId, user.id)
    if not trainer:
      embed = discordservice.CreateEmbed(
          "Trainer Not Started",
          "To start catching and fighting Pokemon that spawn, please begin your journey by using the **/starter[region]** command.",
          ErrorColor)
      await user.send(embed=embed)
      return False

    fighting = reaction.emoji == FightReaction

    if fighting and trainer.UserId not in server.FoughtBy:
      TryFight(server, trainer, spawn.Pokemon_Id)
      return False
    elif not fighting and server.CaughtBy == 0:
      return TryCapture(reaction, server, trainer, spawn)
  except Exception as e:
    print(f"{e}")

def TryCapture(reaction: Reaction, server, trainer, spawn):
  #Update Server to prevent duplicate
  server.CaughtBy = trainer.UserId
  serverservice.UpsertServer(server)

  pokeballId = 1 if reaction.emoji == PokeballReaction else 2 if reaction.emoji == GreatBallReaction else 3
  if pokeballId in trainer.PokeballList:
    #TODO: IMPLEMENT CAPTURE RATE
    ModifyItemList(trainer.PokeballList, pokeballId, -1)
    trainer.OwnedPokemon.append(spawn)
    trainer.TotalCaught += 1
    UpsertTrainer(trainer)
    return True

  #Update Server back to allow capture again
  server.CaughtBy = 0
  serverservice.UpsertServer(server)
  return False

def TryFight(server, trainer, spawnId):
  pokemon = pokemonservice.GetPokemonById(spawnId)
  if not pokemon:
    return

  pkmnId = next((p for p in trainer.Team if p))
  battlePkmn = pokemonservice.GetPokemonById(next((p for p in trainer.OwnedPokemon if p.Id == pkmnId)).Pokemon_Id)
  healthLost = -10 + pokemonservice.PokemonFight(battlePkmn, pokemon, False)

  if trainer.Health >= abs(healthLost) if healthLost < 0 else 0:
    server.FoughtBy.append(trainer.UserId)
    serverservice.UpsertServer(server)
    trainer.Health -= abs(healthLost) if healthLost < 0 else 0
    next((p for p in trainer.OwnedPokemon if p.Id == pkmnId)).GainExp(pokemon.Rarity)
    trainer.Money += (pokemon.Rarity * 50)
    trainer.Fights += 1
    UpsertTrainer(trainer)

#endregion