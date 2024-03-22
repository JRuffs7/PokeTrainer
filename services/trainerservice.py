
from datetime import UTC, datetime, timedelta
import logging
from random import choice
import uuid
from dataaccess import trainerda
from globals import AdminList, GreatBallReaction, PokeballReaction, ShinyOdds, UltraBallReaction, DateFormat, ShortDateFormat
from models.Egg import TrainerEgg
from models.Event import Event
from models.Item import Potion
from models.Trainer import Trainer
from models.Pokemon import Pokemon
from models.enums import EventType, PokemonCount, StatCompare
from services import itemservice, pokemonservice

captureLog = logging.getLogger('capture')


#region Data

def CheckTrainer(serverId: int, userId: int):
  return trainerda.CheckTrainer(serverId, userId)

def GetTrainer(serverId: int, userId: int):
  return trainerda.GetTrainer(serverId, userId)

def UpsertTrainer(trainer: Trainer):
  return trainerda.UpsertTrainer(trainer)

def DeleteTrainer(trainer: Trainer):
  return trainerda.DeleteTrainer(trainer)

def StartTrainer(pokemonId: int, userId: int, serverId: int):
  if(GetTrainer(serverId, userId)):
    return None
  pkmn = pokemonservice.GetPokemonById(pokemonId)
  if not pkmn:
    return None
  spawn = pokemonservice.GenerateSpawnPokemon(pkmn, 5)
  trainer = Trainer.from_dict({
    'UserId': userId,
    'ServerId': serverId,
    'Team': [spawn.Id],
    'Pokedex': [pkmn.PokedexId],
    'Health': 50,
    'Money': 500,
    'Pokeballs': { '1': 5, '2': 0, '3': 0, '4': 0 }
  })
  trainer.OwnedPokemon.append(spawn)
  UpsertTrainer(trainer)
  return trainer

#endregion

#region Inventory/Items

def TryUsePotion(trainer: Trainer, potion: Potion):
  if trainer.Potions[str(potion.Id)] == 0:
    return (False, 0)

  if trainer.Health == 100:
    return (True, 0)

  preHealth = trainer.Health
  trainer.Health += potion.HealingAmount
  if trainer.Health > 100:
    trainer.Health = 100
  ModifyItemList(trainer.Potions, str(potion.Id), -1)
  trainerda.UpsertTrainer(trainer)
  return (True, (trainer.Health - preHealth))

def TryDaily(trainer: Trainer):
  if (not trainer.LastDaily or datetime.strptime(trainer.LastDaily, ShortDateFormat).date() < datetime.now(UTC).date()) or trainer.UserId in AdminList:
    trainer.LastDaily = datetime.now(UTC).strftime(ShortDateFormat)
    ModifyItemList(trainer.Pokeballs, '1', 10)
    trainer.Money += 200
    addEgg = TryAddNewEgg(trainer)
    UpsertTrainer(trainer)
    return addEgg
  return -1

def EventEntry(trainer: Trainer, event: Event):
  #Pokemon Count Event
  if event.EventType == EventType.PokemonCount.value:
    if event.SubType <= 17:
      return sum(PokemonCount(event.SubType).name.lower() in [t.lower() for t in pokemonservice.GetPokemonById(p.Pokemon_Id).Types] for p in trainer.OwnedPokemon)
    elif event.SubType == PokemonCount.Female.value:
      return sum(p.IsFemale for p in trainer.OwnedPokemon)
    elif event.SubType == PokemonCount.Male.value:
      return sum(not p.IsFemale for p in trainer.OwnedPokemon)
    elif event.SubType == PokemonCount.Shiny.value:
      return sum(p.IsShiny for p in trainer.OwnedPokemon)
    else:
      return sum(pokemonservice.GetPokemonById(p.Pokemon_Id).IsLegendary for p in trainer.OwnedPokemon)
  #Stat Compare Event
  else:
    heightBased = event.SubType in [StatCompare.Shortest.value, StatCompare.Tallest.value]
    ordered = GetPokedexList(
      trainer, 
      'height' if heightBased else 'weight',
      0
    )
    if event.SubType in [StatCompare.Tallest.value, StatCompare.Heaviest.value]:
      ordered.reverse()
    return ordered[0]

def EventWinner(trainer: Trainer, ballId: int):
  ModifyItemList(trainer.Pokeballs, str(ballId), 1 if ballId == 4 else 5 if ballId == 3 else 10)
  UpsertTrainer(trainer)

def ModifyItemList(itemDict: dict[str, int], itemId: str, amount: int):
  newAmount = itemDict[itemId] + amount if itemId in itemDict else amount
  if newAmount < 0:
    newAmount = 0
  itemDict.update({ itemId: newAmount })

#endregion

#region Eggs

def TryAddNewEgg(trainer: Trainer):
  if(len(trainer.Eggs) < 5):
    randId = choice(range(1, 101))
    newEggId = 1 if randId <= 65 else 2 if randId <= 95 else 3
    trainer.Eggs.append(TrainerEgg.from_dict({
      'Id': uuid.uuid4().hex,
      'EggId': newEggId
    }))
    return newEggId
  return 0

def EggInteraction(trainer: Trainer):
  updated = False
  for egg in trainer.Eggs:
    if egg.SpawnCount < itemservice.GetEgg(egg.EggId).SpawnsNeeded:
      egg.SpawnCount += 1
      updated = True
  
  if updated:
    UpsertTrainer(trainer)

def CanEggHatch(egg: TrainerEgg):
  return egg.SpawnCount == itemservice.GetEgg(egg.EggId).SpawnsNeeded

def TryHatchEgg(trainer: Trainer, eggId: str):
  egg = next(e for e in trainer.Eggs if e.Id == eggId)
  eggData = itemservice.GetEgg(egg.EggId)
  if egg.SpawnCount < eggData.SpawnsNeeded:
    return None

  trainer.Eggs = [e for e in trainer.Eggs if e.Id != eggId]
  pkmn = choice(pokemonservice.GetPokemonByRarity(eggData.Hatch))
  while pkmn.EvolvesInto and pkmn.Rarity == 3:
    pkmn = choice(pokemonservice.GetPokemonByRarity(eggData.Hatch))
  newPokemon = pokemonservice.GenerateSpawnPokemon(pkmn, 1)
  if not newPokemon.IsShiny:
    newPokemon.IsShiny = choice(range(0, ShinyOdds)) == int(ShinyOdds/2)
  trainer.OwnedPokemon.append(newPokemon)
  trainer.Money += 50
  if len(trainer.Team) < 6:
    trainer.Team.append(newPokemon.Id)
  UpsertTrainer(trainer)
  return newPokemon.Id

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

#endregion

#region Spawn

def CanCallSpawn(trainer: Trainer):
  canSpawn = False
  if not trainer.LastSpawnTime:
    canSpawn = True
  else:
    lastSpawn = datetime.strptime(trainer.LastSpawnTime, DateFormat).replace(tzinfo=UTC)
    if(lastSpawn + timedelta(minutes=1) < datetime.now(UTC)):
      canSpawn = True
  
  if canSpawn:
    trainer.LastSpawnTime = datetime.now(UTC).strftime(DateFormat)
    UpsertTrainer(trainer)
  return canSpawn

def TryCapture(reaction: str, trainer: Trainer, spawn: Pokemon):
  caught = False
  pokeball = itemservice.GetPokeball(1 if reaction == PokeballReaction else 2 if reaction == GreatBallReaction else 3 if reaction == UltraBallReaction else 4)
  pokemon = pokemonservice.GetPokemonById(spawn.Pokemon_Id)
  ModifyItemList(trainer.Pokeballs, str(pokeball.Id), -1)
  if pokemonservice.CaptureSuccess(pokeball, pokemon, spawn.Level):
    trainer.OwnedPokemon.append(spawn)
    trainer.Money += 25
    TryAddToPokedex(trainer, pokemon.PokedexId)
    if len(trainer.Team) < 6:
      trainer.Team.append(spawn.Id)
    caught = True
  UpsertTrainer(trainer)
  return caught

def TryWildFight(trainer: Trainer, wild: Pokemon):
    if trainer.Health <= 0:
      return None
    
    trainerPokemon = next(p for p in trainer.OwnedPokemon if p.Id == trainer.Team[0])
    trainerPkmn = pokemonservice.GetPokemonById(trainerPokemon.Pokemon_Id)
    wildPkmn = pokemonservice.GetPokemonById(wild.Pokemon_Id)
    healthLost = pokemonservice.WildFight(trainerPkmn, wildPkmn, trainerPokemon.Level, wild.Level)
    if healthLost > trainer.Health:
      healthLost = trainer.Health
    trainer.Health -= healthLost
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
    if healthLost < 10 and trainer.Health > 0:
      pokemonservice.AddExperience(
        trainerPokemon, 
        trainerPkmn, 
        wildPkmn.Rarity*wild.Level*2 if wildPkmn.Rarity <= 2 else wildPkmn.Rarity*wild.Level)
      trainer.Money += 50
    UpsertTrainer(trainer)
    return healthLost

#endregion