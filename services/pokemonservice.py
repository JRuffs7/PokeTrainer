import uuid
from math import ceil, floor
from random import choice, uniform, randint
from models.Item import Pokeball
from models.enums import SpecialSpawn

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
    pokemon = choice(pokemonList)
    if not CanSpawn(pokemon):
      pokemon = None

  return GenerateSpawnPokemon(pokemon)

def GetSpecialSpawn():
  spawnType = choice(list(SpecialSpawn))
  pokemonList = pokemonda.GetPokemonByProperty([True], spawnType.value)
  pkmn = choice(pokemonList)
  return GenerateSpawnPokemon(pkmn, 5 if pkmn.IsStarter or (pkmn.IsFossil and pkmn.EvolvesInto) else 75 if pkmn.IsLegendary else 40)

def GenerateSpawnPokemon(pokemon: PokemonData, level: int | None = None):
  shiny = randint(0, ShinyOdds) == int(ShinyOdds / 2)
  height = round(
      uniform(floor(
          (pokemon.Height * 0.9)), ceil((pokemon.Height * 1.1))) / 10, 2)
  weight = round(
      uniform(floor(
          (pokemon.Weight * 0.9)), ceil((pokemon.Weight * 1.1))) / 10, 2)
  female = randint(0, 100) < int(pokemon.FemaleChance / 8 * 100) if pokemon.FemaleChance >= 0 else None
  return Pokemon({
      'Id': uuid.uuid4().hex,
      'Pokemon_Id': pokemon.Id,
      'Height': height if height > 0.00 else 0.01,
      'Weight': weight if weight > 0.00 else 0.01,
      'IsShiny': shiny,
      'IsFemale': female,
      'Level': level if level else choice(range(3,8)) if pokemon.Rarity <= 2 else choice(range(20,26)) if pokemon.Rarity == 3 else choice(range(30,36)),
      'CurrentExp': 0
  })

def GetSpawnList():
  initList = pokemonda.GetPokemonByProperty([1, 2, 3], 'Rarity')
  return [p for p in initList if CanSpawn(p)]

def CanSpawn(pokemon: PokemonData):
  if pokemon.IsMega or pokemon.IsUltraBeast or pokemon.IsParadox or pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsFossil:
    return False
  
  if pokemon.Rarity > 3 or (pokemon.Rarity == 3 and pokemon.EvolvesInto):
    return False
  
  if not pokemon.Sprite and not pokemon.ShinySprite:
    return False
  
  for range in StarterDexIds:
    if pokemon.PokedexId in range:
      return False

  return  True

def CaptureSuccess(pokeball: Pokeball, pokemon: PokemonData, level: int):
  if pokeball.Name == 'Masterball':
    return True

  randInt = choice(range(1,256))
  if level <= 13:
    calc = ceil(((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)*((36-(2*level))/10))
  else:
    calc = ceil((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)

  return randInt < calc

#endregion

#region Trainer Pokemon

def AddExperience(trainerPokemon: Pokemon, pkmnData: PokemonData, exp: int):
  trainerPokemon.CurrentExp += exp
  expNeeded = NeededExperience(trainerPokemon.Level, pkmnData.Rarity, len(pkmnData.EvolvesInto) > 0)
  if trainerPokemon.Level == 100 and trainerPokemon.CurrentExp >= expNeeded:
    trainerPokemon.CurrentExp = expNeeded
  elif trainerPokemon.CurrentExp >= expNeeded:
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

def WildFight(attack: PokemonData, defend: PokemonData, attackLevel: int, defendLevel: int):
  healthLost: list[int] = [1,3,5,7,10,13,15]
  battleResult = TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult >= 2
  doubleDis = battleResult <= -2
  attackGroup = RarityGroup(attack.Rarity, attack.IsLegendary or attack.IsMythical)
  defendGroup = RarityGroup(defend.Rarity, defend.IsLegendary or defend.IsMythical)
  levelAdvantage = 2 if attackLevel > (defendLevel*2) else 1 if attackLevel > (defendLevel*1.5) else 0
  levelDisadvantage = 2 if defendLevel > (attackLevel*2) else 1 if defendLevel > (attackLevel*1.5) else 0
  if attackLevel < 10 and defendLevel < 10:
    levelAdvantage = 1 if levelAdvantage > 0 else 0 
    levelDisadvantage = 1 if levelDisadvantage > 0 else 0 
  
  returnInd = 3

  #legendary
  if attackGroup >= 8:
    if defendGroup == 3:
      returnInd = 2 if attackGroup == 10 else 3 if attackGroup == 9 else 4
    elif defendGroup == 2:
      returnInd = 1 if attackGroup == 10 else 2 if attackGroup == 9 else 3
    else:
      returnInd = 0 if attackGroup == 10 else 1 if attackGroup == 9 else 2
  # 1v1 2v2 3v3
  elif attackGroup - defendGroup == 0:
    returnInd = 2 if doubleAdv else 4 if doubleDis else 3
  # 3v2 2v1
  elif attackGroup - defendGroup == 1:
    returnInd = 1 if doubleAdv else 3 if doubleDis else 2
  # 3v1
  elif attackGroup - defendGroup == 2:
    returnInd = 0 if doubleAdv else 2 if doubleDis else 1
  # 1v2 2v3
  elif attackGroup - defendGroup == -1:
    returnInd = 3 if doubleAdv else 5 if doubleDis else 4
  # 1v3
  else:
    returnInd = 4 if doubleAdv else 6 if doubleDis else 5
  returnInd -= (levelAdvantage - levelDisadvantage)
  return healthLost[0 if returnInd < 0 else returnInd] - (battleResult if not doubleAdv and not doubleDis else 0)

def GymFight(attack: PokemonData, defend: PokemonData):
  battleResult = TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult >= 2
  attackGroup = RarityGroup(attack.Rarity, attack.IsLegendary or attack.IsMythical)
  defendGroup = RarityGroup(defend.Rarity, defend.IsLegendary or defend.IsMythical)

  return doubleAdv and (attackGroup >= defendGroup)

def TypeMatch(attackTypes: list[str], defendTypes: list[str]):
  if len(attackTypes) == 1:
    fightOne = typeservice.TypeWeakness(attackTypes[0].lower(), defendTypes[0].lower())
    fightTwo = typeservice.TypeWeakness(attackTypes[0].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    if fightOne == -2 or fightTwo == -2:
      return -4
    return fightOne + fightTwo
  else:
    fightA1 = typeservice.TypeWeakness(attackTypes[0].lower(), defendTypes[0].lower())
    fightA2 = typeservice.TypeWeakness(attackTypes[0].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    firstType = -4 if fightA1 == -2 or fightA2 == -2 else fightA1 + fightA2 

    fightB1 = typeservice.TypeWeakness(attackTypes[1].lower(), defendTypes[0].lower())
    fightB2 = typeservice.TypeWeakness(attackTypes[1].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    secondType = -4 if fightB1 == -2 or fightB2 == -2 else fightB1 + fightB2 

    #One type is immune
    if firstType == -4 or secondType == -4:
      return firstType if secondType == -4 else secondType
    
    #One type is Super Effective
    if firstType == 2 or secondType == 2:
      return 4 if firstType == 2 and secondType == 2 else 2
    
    return firstType + secondType

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
    'IsShiny': False,
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
      'IsShiny': False,
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

