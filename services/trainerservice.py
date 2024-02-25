from typing import List

from discord import Reaction

from dataaccess import trainerda
from globals import (
    FightReaction,
    GreatBallReaction,
    PokeballReaction,
)
from models.Trainer import Trainer
from models.Pokemon import Pokemon
from services import itemservice, pokemonservice, serverservice, gymservice


def GetTrainer(serverId, userId):
  return trainerda.GetTrainer(serverId, userId)

def UpsertTrainer(trainer):
  return trainerda.UpsertTrainer(trainer)

def DeleteTrainer(trainer):
  return trainerda.DeleteTrainer(trainer)

def StartTrainer(pokemonId: int, userId: int, serverId: int):
  if(GetTrainer(serverId, userId)):
    return None
  pkmn = pokemonservice.GetPokemonById(pokemonId)
  if not pkmn:
    return None
  trainer = Trainer({
      'UserId': userId,
      'ServerId': serverId,
      'Team': [None, None, None, None, None, None],
      'Health': 50,
      'Money': 500,
      'PokeballList': [1,1,1,1,1]
  })
  trainer.OwnedPokemon.append(pokemonservice.GenerateSpawnPokemon(pkmn))
  trainer.OwnedPokemon[0].Level = 5
  trainer.Team[0] = trainer.OwnedPokemon[0].Id
  UpsertTrainer(trainer)
  return trainer

#region Inventory/Items

def GetInventory(trainer: Trainer):
  pkblList = {
      "Pokeball": trainer.PokeballList.count(1),
      "Greatball": trainer.PokeballList.count(2),
      "Ultraball": trainer.PokeballList.count(3),
      "Masterball": trainer.PokeballList.count(4)
  }
  ptnList = {
      "Potion": trainer.PotionList.count(1),
      "Super Potion": trainer.PotionList.count(2),
      "Hyper Potion": trainer.PotionList.count(3),
      "Max Potion": trainer.PotionList.count(4)
  }
  return (trainer.Money, dict(filter(lambda x: x[1] != 0, pkblList.items())),
          dict(filter(lambda x: x[1] != 0, ptnList.items())))

def TryBuyPokeball(trainer: Trainer, ballId, amount):
  ball = itemservice.GetPokeball(ballId)
  if not ball or trainer.Money < (ball.BuyAmount * amount):
    return None

  trainer.Money -= (ball.BuyAmount * amount)
  trainer.PokeballList = ModifyItemList(trainer.PokeballList, ballId, amount)
  trainerda.UpsertTrainer(trainer)
  return ball

def TryBuyPotion(trainer: Trainer, potionId, amount):
  potion = itemservice.GetPotion(potionId)
  if not potion or trainer.Money < (potion.BuyAmount * amount):
    return None

  trainer.Money -= (potion.BuyAmount * amount)
  trainer.PotionList = ModifyItemList(trainer.PotionList, potionId, amount)
  trainerda.UpsertTrainer(trainer)
  return potion

def TrySellPokeball(trainer: Trainer, ballId, amount):
  ball = itemservice.GetPokeball(ballId)
  if not ball or ballId not in trainer.PokeballList:
    return None

  currentNum = len(trainer.PokeballList)
  trainer.PokeballList = ModifyItemList(trainer.PokeballList, ballId,
                                        (0 - amount))
  postModNum = len(trainer.PokeballList)
  trainer.Money += (ball.SellAmount * (currentNum - postModNum))
  trainerda.UpsertTrainer(trainer)
  return { 'NumSold': currentNum - postModNum, 'Item': ball }

def TrySellPotion(trainer: Trainer, potionId, amount):
  potion = itemservice.GetPotion(potionId)
  if not potion or potionId not in trainer.PotionList:
    return None

  currentNum = len(trainer.PotionList)
  trainer.PotionList = ModifyItemList(trainer.PotionList, potionId,
                                      (0 - amount))
  postModNum = len(trainer.PotionList)
  trainer.Money += (potion.SellAmount * (currentNum - postModNum))
  trainerda.UpsertTrainer(trainer)
  return { 'NumSold': (currentNum - postModNum), 'Item': potion }

def TryUsePotion(trainer: Trainer, potion):
  if potion.Id not in trainer.PotionList:
    return (False, 0)

  if trainer.Health == 100:
    return (True, 0)

  preHealth = trainer.Health
  trainer.Health += potion.HealingAmount
  if trainer.Health > 100:
    trainer.Health = 100
  trainer.PotionList = ModifyItemList(trainer.PotionList, potion.Id, -1)
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

def GetPokedexList(trainer: Trainer, orderString: str, shiny: bool):
  pokemonList = trainer.OwnedPokemon
  if shiny == 2:
    pokemonList = [p for p in pokemonList if p.IsShiny]

  match orderString:
    case "height":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Height))
      else:
        pokemonList.sort(key=lambda x: x.Height)
    case "dex":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.IsShiny,pokemonservice.GetPokemonById(x.Pokemon_Id).PokedexId))
      else:
        pokemonList.sort(key=lambda x: pokemonservice.GetPokemonById(x.Pokemon_Id).PokedexId)
    case "name":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.IsShiny,pokemonservice.GetPokemonById(x.Pokemon_Id).Name))
      else:
        pokemonList.sort(key=lambda x: pokemonservice.GetPokemonById(x.Pokemon_Id).Name)
    case "weight":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Weight))
      else:
        pokemonList.sort(key=lambda x: x.Weight)
    case _:
      if shiny == 3:
        pokemonList.sort(key=lambda x: -x.IsShiny)
  return pokemonList

#endregion

#region Team

def GetTeam(trainer: Trainer):
  teamList: List[Pokemon | None] = []
  for pokeId in trainer.Team:
    if pokeId:
      teamList.append(next((p for p in trainer.OwnedPokemon if p.Id == pokeId), None))
  return teamList

def SetTeamSlot(trainer: Trainer, slotNum: int, pokemonId: str):
  trainer.Team[slotNum] = pokemonId
  UpsertTrainer(trainer)

def Evolve(trainer: Trainer, initialPkmn: Pokemon, evolveId: int):
  newPkmn = pokemonservice.EvolvePokemon(initialPkmn, evolveId)
  index = trainer.OwnedPokemon.index(initialPkmn)
  trainer.OwnedPokemon[index] = newPkmn
  UpsertTrainer(trainer)
  return newPkmn

def ReleasePokemon(trainer: Trainer, pokemonIds: list[str]):
  released = next(p for p in trainer.OwnedPokemon if p.Id in pokemonIds)
  trainer.OwnedPokemon = [p for p in trainer.OwnedPokemon if p.Id not in pokemonIds]
  UpsertTrainer(trainer)
  return pokemonservice.GetPokemonById(released.Pokemon_Id).Name

#endregion

#region Gym Badges

def GetGymBadges(trainer: Trainer, generation: int):
  badgeList = [gymservice.GetBadgeById(b) for b in trainer.Badges]
  if generation:
    badgeList = [b for b in badgeList if b.Generation == generation]
  return badgeList

#endregion

#region REACTION

async def ReationReceived(bot, user, reaction):
  message = reaction.message
  server = serverservice.GetServer(message.guild.id)
  users = [user async for user in reaction.users()]
  #Not a supported reaction
  if not users.__contains__(bot.user) or server is None:
    await reaction.remove(user)
    return False

  #Not a reaction on the last spawn pokemon or no spawn at all
  if reaction.message.id != server.LastSpawnMessage or not server.LastSpawned:
    await reaction.remove(user)
    return False

  spawn = server.LastSpawned
  trainer = GetTrainer(server.ServerId, user.id)
  if not trainer:
    await reaction.remove(user)
    return False

  fighting = reaction.emoji == FightReaction

  if fighting and trainer.Health > 0 and trainer.UserId not in server.FoughtBy:
    TryWildFight(server, trainer, spawn.Pokemon_Id)
    return False
  elif not fighting and server.CaughtBy == 0:
    if not TryCapture(reaction, server, trainer, spawn):
      await reaction.remove(user)
      return False
    return True
  await reaction.remove(user)
  return False

def TryCapture(reaction: Reaction, server, trainer: Trainer, spawn: Pokemon):
  #Update Server to prevent duplicate
  server.CaughtBy = trainer.UserId
  serverservice.UpsertServer(server)

  pokeballId = 1 if reaction.emoji == PokeballReaction else 2 if reaction.emoji == GreatBallReaction else 3
  if pokeballId in trainer.PokeballList:
    #TODO: IMPLEMENT CAPTURE RATE
    ModifyItemList(trainer.PokeballList, pokeballId, -1)
    trainer.OwnedPokemon.append(spawn)
    UpsertTrainer(trainer)
    return True

  #Update Server back to allow capture again
  server.CaughtBy = 0
  serverservice.UpsertServer(server)
  return False

def TryWildFight(server, trainer: Trainer, spawnPokemon_Id: int):
    spawnPokemon = pokemonservice.GetPokemonById(spawnPokemon_Id)
    trainerPokemon = next(p for p in trainer.OwnedPokemon if p.Id == pkmnId)
    if not spawnPokemon:
      return

    pkmnId = next((p for p in trainer.Team if p))
    battlePkmn = pokemonservice.GetPokemonById(trainerPokemon.Pokemon_Id)
    battleResult = pokemonservice.PokemonFight(battlePkmn, spawnPokemon)
    healthLost = battleResult - 6

    server.FoughtBy.append(trainer.UserId)
    serverservice.UpsertServer(server)
    trainer.Health += healthLost
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
    if healthLost > -10:
      pokemonservice.AddExperience(trainerPokemon, battlePkmn.Rarity, spawnPokemon.Rarity)
      trainer.Money += 50
    UpsertTrainer(trainer)

#endregion