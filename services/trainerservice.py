
from math import ceil
from random import choice
from dataaccess import trainerda
from globals import GreatBallReaction, PokeballReaction, UltraBallReaction
from models.Item import Pokeball, Potion
from models.Trainer import Trainer
from models.Pokemon import Pokemon, PokemonData
from services import itemservice, pokemonservice


#region Data

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
    'Pokeballs': { '1': 5, '2': 0, '3': 0, '4': 0 },
    'Potions': { '1': 0, '2': 0, '3': 0, '4': 0 },
    'LastSpawnTime': None
  })
  trainer.OwnedPokemon.append(spawn)
  UpsertTrainer(trainer)
  return trainer

#endregion

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
  ModifyItemList(trainer.Potions, str(potion.Id), -1)
  trainerda.UpsertTrainer(trainer)
  return (True, (trainer.Health - preHealth))

def ModifyItemList(itemDict: dict[str, int], itemId: str, amount: int):
  newAmount = itemDict[itemId] + amount
  if newAmount < 0:
    newAmount = 0
  itemDict.update({ itemId: newAmount if newAmount > 0 else 0 })
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

def TryCapture(reaction: str, trainer: Trainer, spawn: Pokemon):
  caught = False
  pokeball = itemservice.GetPokeball(1 if reaction == PokeballReaction else 2 if reaction == GreatBallReaction else 3 if reaction == UltraBallReaction else 4)
  pokemon = pokemonservice.GetPokemonById(spawn.Pokemon_Id)
  ModifyItemList(trainer.Pokeballs, str(pokeball.Id), -1)
  if CaptureSuccess(pokeball, pokemon, spawn.Level):
    trainer.OwnedPokemon.append(spawn)
    TryAddToPokedex(trainer, pokemon.PokedexId)
    caught = True
  UpsertTrainer(trainer)
  return caught

def CaptureSuccess(pokeball: Pokeball, pokemon: PokemonData, level: int):
  if pokeball.Name == 'Masterball':
    return True

  randInt = choice(range(1,256))
  if level <= 13:
    calc = ceil(((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)*((36-(2*level))/10))
  else:
    calc = ceil((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)

  print(f"{randInt} / {calc}")
  return randInt < calc
    

def TryWildFight(trainer: Trainer, wild: Pokemon):
    if trainer.Health <= 0:
      return None
    
    trainerPokemon = next(p for p in trainer.OwnedPokemon if p.Id == trainer.Team[0])
    trainerPkmn = pokemonservice.GetPokemonById(trainerPokemon.Pokemon_Id)
    wildPkmn = pokemonservice.GetPokemonById(wild.Pokemon_Id)
    healthLost = pokemonservice.WildFight(trainerPkmn, wildPkmn)
    if healthLost > trainer.Health:
      healthLost = trainer.Health
    trainer.Health -= healthLost
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
    if healthLost <= 10 and trainer.Health > 0:
      pokemonservice.AddExperience(trainerPokemon, trainerPkmn, wildPkmn.Rarity)
      trainer.Money += 50
    UpsertTrainer(trainer)
    return healthLost

#endregion