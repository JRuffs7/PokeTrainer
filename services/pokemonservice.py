from itertools import chain
import math
import random
import uuid

from services import typeservice
from dataaccess import pokemonda
from globals import FemaleSign, MaleSign, ShinyOdds, ShinySign, StarterDexIds
from models.Pokemon import PokemonData, Pokemon

#region Data

def GetAllPokemon():
  return pokemonda.GetAllPokemon()


def GetPokemonById(id: int):
  results = pokemonda.GetPokemonByProperty([id], 'Id')
  if results:
    return results.pop()
  return None


def GetPokemonCount():
  return len(set(p.PokedexId for p in GetAllPokemon()))


def GetPokemonColors():
  return pokemonda.GetUniquePokemonProperty('Color')


def GetPokemonByColor(color: str):
  return pokemonda.GetPokemonByProperty([color], 'Color')


def GetPokemonByType(type: str):
  pokeList = pokemonda.GetPokemonByType(type)
  singleType = [x for x in pokeList if len(x.Types) == 1]
  firstType = [x for x in pokeList if len(x.Types) == 2 and x.Types[0].lower() == type]
  secondType = [x for x in pokeList if len(x.Types) == 2 and x.Types[1].lower() == type]
  singleType.sort(key=lambda x: x.Name)
  firstType.sort(key=lambda x: x.Name)
  secondType.sort(key=lambda x: x.Name)

  return singleType+firstType+secondType

#endregion

#region Display

def GetPokemonDisplayName(pokemon: Pokemon, showGender: bool = True, showShiny: bool = True):
  pkmn = GetPokemonById(pokemon.Pokemon_Id)
  return f"{pkmn.Name}{GetNameEmojis(pokemon, showGender, showShiny)}"


def GetNameEmojis(pokemon: Pokemon, showGender: bool, showShiny: bool):
    genderEmoji = f"{f' {FemaleSign}' if pokemon.IsFemale == True else f' {MaleSign}' if pokemon.IsFemale == False else ''}" if showGender else ""
    shinyEmoji = f"{f'{ShinySign}' if pokemon.IsShiny else ''}" if showShiny else ""
    return f"{genderEmoji}{shinyEmoji}"


def GetOwnedPokemonDescription(pokemon: Pokemon):
  pkmn = GetPokemonById(pokemon.Pokemon_Id)
  return f"Lvl. {pokemon.Level} ({pokemon.CurrentExp}/{(50 * pkmn.Rarity) if pkmn.Rarity <= 3 else 250}xp) | H:{pokemon.Height} | W:{pokemon.Weight} | Types: {'/'.join(pkmn.Types)}"


def GetPokemonImage(pokemon: Pokemon | PokemonData):
  pkmn = GetPokemonById(pokemon.Pokemon_Id)
  if pokemon.IsShiny and pokemon.IsFemale:
      return pkmn.ShinySpriteFemale or pkmn.ShinySprite
  elif pokemon.IsShiny and not pokemon.IsFemale:
    return pkmn.ShinySprite
  elif not pokemon.IsShiny and pokemon.IsFemale:
    return pkmn.SpriteFemale or pkmn.Sprite
  return pkmn.Sprite

#endregion

#region Spawns

def SpawnPokemon():
  pokemonList = pokemonda.GetPokemonByProperty([1, 2, 3], 'Rarity')
  pokemon = None
  while not pokemon:
    pokemon = random.choice(pokemonList)
    if not CanSpawn(pokemon):
      pokemon = None

  return GenerateSpawnPokemon(pokemon)

def GenerateSpawnPokemon(pokemon: PokemonData, level: int | None = None):
  shiny = random.randint(0, ShinyOdds) == int(ShinyOdds / 2)
  height = round(
      random.uniform(math.floor(
          (pokemon.Height * 0.9)), math.ceil((pokemon.Height * 1.1))) / 10, 2)
  weight = round(
      random.uniform(math.floor(
          (pokemon.Weight * 0.9)), math.ceil((pokemon.Weight * 1.1))) / 10, 2)
  female = random.randint(0, 100) < int(pokemon.FemaleChance / 8 *
                                        100) if pokemon.FemaleChance else None
  return Pokemon({
      'Id': uuid.uuid4().hex,
      'Pokemon_Id': pokemon.Id,
      'Height': height if height > 0.00 else 0.01,
      'Weight': weight if weight > 0.00 else 0.01,
      'IsShiny': shiny,
      'IsFemale': female,
      'Level': level if level else random.choice(range(1,6)) if pokemon.Rarity <= 2 else random.choice(range(20,26)) if pokemon.Rarity == 3 else random.choice(range(30,36)),
      'CurrentExp': 0
  })

def GetSpawnList():
  initList = pokemonda.GetPokemonByProperty([1, 2, 3], 'Rarity')
  return [p for p in initList if CanSpawn(p)]

def CanSpawn(pokemon: PokemonData):
  if pokemon.IsMega or pokemon.IsUltraBeast or pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsFossil:
    return False
  
  if pokemon.Rarity > 3 or (pokemon.Rarity == 3 and pokemon.EvolvesInto):
    return False
  
  if not pokemon.Sprite and not pokemon.ShinySprite:
    return False
  
  for range in StarterDexIds:
    if pokemon.PokedexId in range:
      return False

  return  True


#endregion

#region Trainer Pokemon

def AddExperience(trainerPokemon: Pokemon, pkmnData: PokemonData, exp: int):
  trainerPokemon.CurrentExp += exp
  expNeeded = NeededExperience(trainerPokemon.Level, pkmnData.Rarity, len(pkmnData.EvolvesInto) > 0)
  if trainerPokemon.Level == 100 and trainerPokemon.CurrentExp > expNeeded:
    trainerPokemon.CurrentExp = expNeeded
  elif trainerPokemon.CurrentExp > expNeeded:
      trainerPokemon.Level += 1
      trainerPokemon.CurrentExp -= expNeeded

def NeededExperience(level: int, rarity: int, canEvolve: bool):
  if rarity == 1:
    return 50 if level < 20 else 150 if level < 35 else 250
  if rarity == 2:
    return 100 if level < 30 else 250
  if rarity == 3 and canEvolve:
    return 150 if level < 35 else 250
  if rarity == 4 or rarity == 5:
    return 250
  if (rarity == 3 and not canEvolve) or rarity >= 8:
    return 200

def CanTrainerPokemonEvolve(pkmn: Pokemon):
  pkmnData = GetPokemonById(pkmn.Pokemon_Id)
  if pkmnData.Rarity == 1 and len(pkmnData.EvolvesInto) >= 1:
    return pkmn.Level >= 20
  elif pkmnData.Rarity == 2 and len(pkmnData.EvolvesInto) >= 1:
    return pkmn.Level >= 30
  elif pkmnData.Rarity == 3 and len(pkmnData.EvolvesInto) >= 1:
    return pkmn.Level >= 35
  return False


def EvolvePokemon(initial: Pokemon, evolveId: int):
  spawn = GenerateSpawnPokemon(GetPokemonById(evolveId))
  return Pokemon({
      'Id': initial.Id,
      'Pokemon_Id': evolveId,
      'Height': spawn.Height,
      'Weight': spawn.Weight,
      'IsShiny': initial.IsShiny,
      'IsFemale': initial.IsFemale,
      'Level': initial.Level,
      'CurrentExp': initial.CurrentExp
    })

#endregion

#region Fights

def WildFight(attack: PokemonData, defend: PokemonData):
  battleResult = TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult == 2
  doubleDis = battleResult <= -2
  attackGroup = RarityGroup(attack.Rarity, attack.IsLegendary or attack.IsMythical)
  defendGroup = RarityGroup(defend.Rarity, defend.IsLegendary or defend.IsMythical)

  #legendary
  if attackGroup >= 8:
    if defendGroup == 3:
      return 5 if attackGroup == 10 else 10 if attackGroup == 9 else 15
    elif defendGroup == 2:
      return 3 if attackGroup == 10 else 5 if attackGroup == 9 else 10
    else:
      return 1 if attackGroup == 10 else 3 if attackGroup == 9 else 5
    
  # 1v1 2v2 3v3
  if attackGroup - defendGroup == 0:
    groupRes = 5 if doubleAdv else 15 if doubleDis else 10 - battleResult
  # 3v2 2v1
  elif attackGroup - defendGroup == 1:
    groupRes = 3 if doubleAdv else 10 if doubleDis else 5 - battleResult
  # 3v1
  elif attackGroup - defendGroup == 2:
    groupRes = 1 if doubleAdv else 5 if doubleDis else 3
  # 1v2 2v3
  elif attackGroup - defendGroup == -1:
    groupRes = 10 if doubleAdv else 20 if doubleDis else 15 - battleResult
  # 1v3
  else:
    groupRes = 15 if doubleAdv else 25 if doubleDis else 20
  return groupRes

def GymFight(attack: PokemonData, defend: PokemonData):
  battleResult = TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult == 2
  attackGroup = RarityGroup(attack.Rarity, attack.IsLegendary or attack.IsMythical)
  defendGroup = RarityGroup(defend.Rarity, defend.IsLegendary or defend.IsMythical)

  return doubleAdv and (attackGroup >= defendGroup)

def TypeMatch(attackTypes: list[str], defendTypes: list[str]):
  fightTotal = typeservice.TypeWeakness(attackTypes[0].lower(), defendTypes[0].lower())
  fightTotal += typeservice.TypeWeakness(
    attackTypes[1].lower() if len(attackTypes) > 1 else attackTypes[0].lower(),
    defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
  return fightTotal

def RarityGroup(rarity: int, isLegendary: bool):
  rarityGroup = 1 if rarity <= 2 else 2 if rarity == 3 else 3
  if isLegendary:
    rarityGroup = rarity
  return rarityGroup

#endregion

def GeneratePokemonSearchGroup(pokemonId):
  pkmn = GetPokemonById(pokemonId)
  if not pkmn:
    return None
  pkmnList: list[Pokemon] = []
  pkmnList.append(Pokemon({
    'Pokemon_Id': pokemonId,
    'Height': pkmn.Height,
    'Weight': pkmn.Weight,
    'IsFemale': pkmn.FemaleChance == 8,
  }))
  if pkmn.ShinySprite:
    pkmnList.append(Pokemon({
    'Pokemon_Id': pokemonId,
    'Height': pkmn.Height,
    'Weight': pkmn.Weight,
    'IsShiny': True,
    'IsFemale': pkmn.FemaleChance == 8,
  }))
  if pkmn.SpriteFemale and pkmn.FemaleChance != 0:
    pkmnList.append(Pokemon({
      'Pokemon_Id': pokemonId,
      'Height': pkmn.Height,
      'Weight': pkmn.Weight,
      'IsFemale': True,
    }))
  if pkmn.ShinySpriteFemale and pkmn.FemaleChance != 0:
    pkmnList.append(Pokemon({
      'Pokemon_Id': pokemonId,
      'Height': pkmn.Height,
      'Weight': pkmn.Weight,
      'IsShiny': True,
      'IsFemale': True,
    }))
  return pkmnList

