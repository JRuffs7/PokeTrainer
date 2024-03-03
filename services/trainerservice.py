from typing import List

from discord import Reaction

from dataaccess import trainerda
from globals import (
    FightReaction,
    GreatBallReaction,
    PokeballReaction,
)
from models.Item import Potion
from models.Trainer import Trainer
from models.Pokemon import Pokemon
from services import pokemonservice, serverservice, gymservice


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
  spawn = pokemonservice.GenerateSpawnPokemon(pkmn, 5)
  trainer = Trainer({
    'UserId': userId,
    'ServerId': serverId,
    'Team': [spawn.Id],
    'OwnedPokemon': [],
    'Pokedex': [pkmn.PokedexId],
    'Badges': [],
    'Health': 50,
    'Money': 500,
    'PokeballList': { '1': 5, '2': 0, '3': 0, '4': 0 },
    'PotionList': { '1': 0, '2': 0, '3': 0, '4': 0 },
    'LastSpawnTime': None
  })
  trainer.OwnedPokemon.append(spawn)
  UpsertTrainer(trainer)
  return trainer

#region Inventory/Items

def GetInventory(trainer: Trainer):
  pkblList = {
      "Pokeball": trainer.Pokeballs['1'],
      "Greatball": trainer.Pokeballs['2'],
      "Ultraball": trainer.Pokeballs['3'],
      "Masterball": trainer.Pokeballs['4']
  }
  ptnList = {
      "Potion": trainer.Potions['1'],
      "Super Potion": trainer.Potions['2'],
      "Hyper Potion": trainer.Potions['3'],
      "Max Potion": trainer.Potions['4']
  }
  return (trainer.Money, dict(filter(lambda x: x[1] != 0, pkblList.items())),
          dict(filter(lambda x: x[1] != 0, ptnList.items())))

def TryUsePotion(trainer: Trainer, potion: Potion):
  if trainer.Potions[str(potion.Id)] == 0:
    return (False, 0)

  if trainer.Health == 100:
    return (True, 0)

  preHealth = trainer.Health
  trainer.Health += potion.HealingAmount
  if trainer.Health > 100:
    trainer.Health = 100
  ModifyItemList(trainer.Potions, potion.Id, -1)
  trainerda.UpsertTrainer(trainer)
  return (True, (trainer.Health - preHealth))

def ModifyItemList(itemDict: dict[str, int], itemId: int, amount: int):
  newAmount = itemDict[str(itemId)] + amount
  if newAmount < 0:
    newAmount = 0
  itemDict.update({ str(itemId): newAmount if newAmount > 0 else 0 })
  return (amount + newAmount) if newAmount < 0 else amount

#endregion

#region Pokedex

def GetPokedexList(trainer: Trainer, orderString: str, shiny: int):
  pokemonList = [p for p in trainer.OwnedPokemon]
  if shiny == 1:
    pokemonList = [p for p in pokemonList if p.IsShiny]

  match orderString:
    case "height":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Height))
      else:
        pokemonList.sort(key=lambda x: x.Height)
    case "dex":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,pokemonservice.GetPokemonById(x.Pokemon_Id).PokedexId,x.Pokemon_Id))
      else:
        pokemonList.sort(key=lambda x: (pokemonservice.GetPokemonById(x.Pokemon_Id).PokedexId,x.Pokemon_Id))
    case "name":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,pokemonservice.GetPokemonById(x.Pokemon_Id).Name))
      else:
        pokemonList.sort(key=lambda x: pokemonservice.GetPokemonById(x.Pokemon_Id).Name)
    case "weight":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Weight))
      else:
        pokemonList.sort(key=lambda x: x.Weight)
    case "level":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,-x.Level,x.Pokemon_Id))
      else:
        pokemonList.sort(key=lambda x: (-x.Level,x.Pokemon_Id))
    case _:
      if shiny == 2:
        pokemonList.sort(key=lambda x: -x.IsShiny)
  return pokemonList

def TryAddToPokedex(trainer: Trainer, pokedexId: int):
  if pokedexId not in trainer.Pokedex:
    trainer.Pokedex.append(pokedexId)

#endregion

#region Team

def GetTeam(trainer: Trainer):
  return [next(p for p in trainer.OwnedPokemon if p.Id == pokeId) for pokeId in trainer.Team]

def SetTeamSlot(trainer: Trainer, slotNum: int, pokemonId: str):
  #swapping
  if pokemonId in trainer.Team:
    currentSlot = trainer.Team.index(pokemonId)
    currentPkmn = trainer.Team[slotNum]
    trainer.Team[currentSlot] = currentPkmn
    trainer.Team[slotNum] = pokemonId
  #adding
  elif slotNum == len(trainer.Team):
    trainer.Team.append(pokemonId)
  #replacing
  else:
    trainer.Team[slotNum] = pokemonId
  UpsertTrainer(trainer)

def Evolve(trainer: Trainer, initialPkmn: Pokemon, evolveId: int):
  newPkmn = pokemonservice.EvolvePokemon(initialPkmn, evolveId)
  index = trainer.OwnedPokemon.index(initialPkmn)
  trainer.OwnedPokemon[index] = newPkmn
  TryAddToPokedex(trainer, pokemonservice.GetPokemonById(newPkmn.Pokemon_Id).PokedexId)
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
  badgeList = [ba for ba in [gymservice.GetBadgeById(b) for b in trainer.Badges] if ba]
  if generation:
    badgeList = [b for b in badgeList if b.Generation == generation]
  badgeList.sort(key=lambda x: x.Id)
  return badgeList

def GymCompletion(trainer: Trainer, generation: int = None):
  allBadges = [b.Id for b in gymservice.GetAllBadges() if (b.Generation == generation if generation else True)]
  obtained = list(filter(allBadges.__contains__, trainer.Badges))
  return (len(obtained), len(allBadges))

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
  if trainer.PokeballList.get(pokeballId) > 0:
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