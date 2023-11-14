from typing import List

from discord import Reaction

from dataaccess import trainerda
from globals import (
    FightReaction,
    GreatBallReaction,
    PokeballReaction,
)
from models.Trainer import Trainer
from models.Pokemon import SpawnPokemon
from services import itemservice, pokemonservice, serverservice


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
  trainer = Trainer({
      'UserId': userId,
      'ServerId': serverId,
      'Team': [None, None, None, None, None, None],
      'Health': 50,
      'Money': 500,
      'PokeballList': [1,1,1,1,1]
  })
  trainer = AddNewOwnedPokemon(trainer, pokemonservice.GenerateSpawnPokemon(pkmn))
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

def AddNewOwnedPokemon(trainer: Trainer, pokemon: SpawnPokemon):
  trainer.OwnedPokemon.append(pokemonservice.ConvertSpawnPokemonToPokedexEntry(pokemon))
  return trainer

def GetPokedexList(trainer: Trainer, orderString, shiny):
  pokemonList = trainer.OwnedPokemon
  if shiny == 2:
    pokemonList = [p for p in pokemonList if p.Pokemon.IsShiny]

  match orderString:
    case "height":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Pokemon.Height))
      else:
        pokemonList.sort(key=lambda x: x.Pokemon.Height)
    case "dex":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.Pokemon.IsShiny,x.PokedexId))
      else:
        pokemonList.sort(key=lambda x: x.PokedexId)
    case "name":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Name))
      else:
        pokemonList.sort(key=lambda x: x.Name)
    case "weight":
      if shiny == 3:
        pokemonList.sort(key=lambda x: (-x.Pokemon.IsShiny,x.Pokemon.Weight))
      else:
        pokemonList.sort(key=lambda x: x.Pokemon.Weight)
    case _:
      if shiny == 3:
        pokemonList.sort(key=lambda x: -x.Pokemon.IsShiny)
  return pokemonList

#endregion

#region Team

def GetTeam(trainer: Trainer):
  teamList = []
  for ind, pokeId in enumerate(trainer.Team):
    if pokeId:
      mon = next((p for p in trainer.OwnedPokemon if pokeId and p.Id == pokeId))
      mon.Name = f"({ind + 1}) {mon.Name}"
      teamList.append(mon)
  return teamList

def SetTeamSlot(trainer: Trainer, slotNum, pokemonId):
  trainer.Team[slotNum] = pokemonId
  UpsertTrainer(trainer)

def Evolve(trainer: Trainer, initialPkmn, evolveId):
  newPkmn = pokemonservice.EvolvePokemon(initialPkmn, evolveId)
  index = trainer.OwnedPokemon.index(initialPkmn)
  trainer.OwnedPokemon[index] = newPkmn
  UpsertTrainer(trainer)
  return newPkmn

def ReleasePokemon(trainer: Trainer, pokemonIds):
  released = next((p for p in trainer.OwnedPokemon if p.Id in pokemonIds), None)
  trainer.OwnedPokemon = [p for p in trainer.OwnedPokemon if p.Id not in pokemonIds]
  UpsertTrainer(trainer)
  return released.Name

#endregion

#region Gym Badges

def GetNextTrainerGym(trainer: Trainer):
  currBadges = trainer.Badges

  next


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

def TryCapture(reaction: Reaction, server, trainer, spawn):
  #Update Server to prevent duplicate
  server.CaughtBy = trainer.UserId
  serverservice.UpsertServer(server)

  pokeballId = 1 if reaction.emoji == PokeballReaction else 2 if reaction.emoji == GreatBallReaction else 3
  if pokeballId in trainer.PokeballList:
    #TODO: IMPLEMENT CAPTURE RATE
    ModifyItemList(trainer.PokeballList, pokeballId, -1)
    trainer = AddNewOwnedPokemon(trainer, spawn)
    trainer.TotalCaught += 1
    UpsertTrainer(trainer)
    return True

  #Update Server back to allow capture again
  server.CaughtBy = 0
  serverservice.UpsertServer(server)
  return False

def TryWildFight(server, trainer, spawnId):
    pokemon = pokemonservice.GetPokemonById(spawnId)
    if not pokemon:
      return

    pkmnId = next((p for p in trainer.Team if p))
    battlePkmn = pokemonservice.GetPokemonById(next((p for p in trainer.OwnedPokemon if p.Id == pkmnId)).Pokemon.Pokemon_Id)
    battleResult = pokemonservice.PokemonFight(battlePkmn, pokemon)
    healthLost = battleResult - 6

    server.FoughtBy.append(trainer.UserId)
    serverservice.UpsertServer(server)
    trainer.Health += healthLost
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
    if healthLost > -10:
      next((p for p in trainer.OwnedPokemon if p.Id == pkmnId)).GainExp(pokemon.Rarity)
      trainer.Money += 50
      trainer.Fights += 1
    UpsertTrainer(trainer)

#endregion