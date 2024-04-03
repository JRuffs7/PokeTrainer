import uuid
from math import ceil, floor
from random import choice, uniform
from models.Item import Pokeball
from models.Zone import Zone
from models.enums import SpecialSpawn

from services import typeservice
from dataaccess import pokemonda
from globals import FemaleSign, MaleSign, ShinyOdds, ShinySign
from models.Pokemon import PokemonData, Pokemon

#region Data

def GetAllPokemon():
  return pokemonda.GetAllPokemon()


def GetPokemonById(id: int):
  results = pokemonda.GetPokemonByProperty([id], 'Id')
  if results:
    return results.pop()
  return None

def GetPokemonByIdList(idList: list[int]):
  return pokemonda.GetPokemonByProperty(idList, 'Id')

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

def GetPokemonByRarity(rarity: list[int]):
  return pokemonda.GetPokemonByProperty(rarity, 'Rarity')

def GetStarterPokemon():
  return [p for p in pokemonda.GetAllPokemon() if p.IsStarter]

def IsSpecialPokemon(pokemon: PokemonData):
  return pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsUltraBeast

#endregion

#region Display

def GetPokemonDisplayName(pokemon: Pokemon, data: PokemonData = None, showGender: bool = True, showShiny: bool = True):
  pkmn = GetPokemonById(pokemon.Pokemon_Id) if not data else data
  genderEmoji = f"{f' {FemaleSign}' if pokemon.IsFemale == True else f' {MaleSign}' if pokemon.IsFemale == False else ''}" if showGender else ""
  shinyEmoji = f"{f'{ShinySign}' if pokemon.IsShiny else ''}" if showShiny else ""
  return f"{pkmn.Name}{genderEmoji}{shinyEmoji}"


def GetOwnedPokemonDescription(pokemon: Pokemon, pkmnData: PokemonData = None):
  pkmn = GetPokemonById(pokemon.Pokemon_Id) if not pkmnData else pkmnData
  return f"Lvl. {pokemon.Level} ({pokemon.CurrentExp}/{NeededExperience(pokemon.Level, pkmn.Rarity, len(pkmn.EvolvesInto) > 0)}xp | H:{pokemon.Height} | W:{pokemon.Weight} | Types: {'/'.join(pkmn.Types)}"


def GetPokemonImage(pokemon: Pokemon, pkmnData: PokemonData = None):
  pkmn = GetPokemonById(pokemon.Pokemon_Id) if not pkmnData else pkmnData
  if pokemon.IsShiny and pokemon.IsFemale:
      return pkmn.ShinySpriteFemale or pkmn.ShinySprite
  elif pokemon.IsShiny and not pokemon.IsFemale:
    return pkmn.ShinySprite
  elif not pokemon.IsShiny and pokemon.IsFemale:
    return pkmn.SpriteFemale or pkmn.Sprite
  return pkmn.Sprite

#endregion

#region Spawns

def SpawnPokemon(specialZone: Zone|None, badgeBonus: int):
  pokemonList = pokemonda.GetPokemonByProperty([1, 2, 3], 'Rarity')
  if specialZone:
    specialTypes = [t.lower() for t in specialZone.Types]
    pokemonList = [p for p in pokemonList if p.Types[0].lower() in specialTypes or (p.Types[1].lower() in specialTypes if len(p.Types) > 1 else False)]
  pokemon = None
  while not pokemon:
    pokemon = choice(pokemonList)
    if not CanSpawn(pokemon):
      pokemon = None

  spawn = GenerateSpawnPokemon(pokemon)
  spawn.Level += floor(badgeBonus/2)
  return spawn

def GetSpecialSpawn():
  spawnType = choice(list(SpecialSpawn))
  pokemonList = pokemonda.GetPokemonByProperty([True], spawnType.value)
  pkmn = None
  while not pkmn:
    pkmn = choice(pokemonList)
    if pkmn.IsFossil and pkmn.EvolvesInto:
      pkmn = None
  return GenerateSpawnPokemon(pkmn, 5 if pkmn.IsStarter or pkmn.IsFossil else 75 if pkmn.IsLegendary or pkmn.IsMythical else 40)

def GenerateSpawnPokemon(pokemon: PokemonData, level: int | None = None):
  shiny = choice(range(0, ShinyOdds)) == int(ShinyOdds / 2)
  height = round(
      uniform(floor(
          (pokemon.Height * 0.9)), ceil((pokemon.Height * 1.1))) / 10, 2)
  weight = round(
      uniform(floor(
          (pokemon.Weight * 0.9)), ceil((pokemon.Weight * 1.1))) / 10, 2)
  female = choice(range(0, 100)) < int(pokemon.FemaleChance / 8 * 100) if pokemon.FemaleChance >= 0 else None
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

def CanSpawn(pokemon: PokemonData):
  if pokemon.IsMega or pokemon.IsUltraBeast or pokemon.IsParadox or pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsFossil:
    return False
  
  if pokemon.Rarity > 3 or (pokemon.Rarity == 3 and pokemon.EvolvesInto):
    return False
  
  if not pokemon.Sprite and not pokemon.ShinySprite:
    return False
  
  for pkmn in GetStarterPokemon():
    if pkmn.PokedexId <= pokemon.PokedexId <= pkmn.PokedexId+2:
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
  while trainerPokemon.CurrentExp >= expNeeded and trainerPokemon.Level < 100:
    trainerPokemon.Level += 1
    trainerPokemon.CurrentExp -= expNeeded
    expNeeded = NeededExperience(trainerPokemon.Level, pkmnData.Rarity, len(pkmnData.EvolvesInto) > 0)

  if trainerPokemon.Level == 100 and trainerPokemon.CurrentExp > expNeeded:
    excess = trainerPokemon.CurrentExp - expNeeded
    trainerPokemon.CurrentExp = expNeeded
    return excess

def NeededExperience(level: int, rarity: int, canEvolve: bool):
  if rarity == 1:
    return 50 if level < 20 else 150 if level < 35 else 250
  if rarity == 2:
    return 100 if level < 30 else 250
  if rarity == 3 and canEvolve:
    return 150 if level < 35 else 250
  if rarity == 4 or rarity == 5:
    return 250
  #if (rarity == 3 and not canEvolve) or rarity >= 8:
  return 200

def CanPokemonEvolve(pkmn: PokemonData, level: int):
  if pkmn.Rarity == 1 and len(pkmn.EvolvesInto) >= 1:
    return level >= 20
  elif pkmn.Rarity == 2 and len(pkmn.EvolvesInto) >= 1:
    return level >= 30
  elif pkmn.Rarity == 3 and len(pkmn.EvolvesInto) >= 1:
    return level >= 35
  return False

def EvolvePokemon(initial: Pokemon, evolve: PokemonData):
  spawn = GenerateSpawnPokemon(evolve)
  return Pokemon({
      'Id': initial.Id,
      'Pokemon_Id': evolve.Id,
      'Height': spawn.Height,
      'Weight': spawn.Weight,
      'IsShiny': initial.IsShiny,
      'IsFemale': initial.IsFemale,
      'Level': initial.Level,
      'CurrentExp': initial.CurrentExp
    })

def GetPokemonThatCanEvolve(ownedPokemon: list[Pokemon]):
  if not ownedPokemon:
    return None
  dataList = GetPokemonByIdList([p.Pokemon_Id for p in ownedPokemon])
  return [p for p in ownedPokemon if CanPokemonEvolve(next(pk for pk in dataList if pk.Id == p.Pokemon_Id), p.Level)]

def SimulateLevelGain(currLevel: int, currExp: int, rarity: int, canEvolve: bool, exp: int):
  simPokemon = Pokemon({'Level': currLevel, 'CurrentExp': currExp})
  simData = PokemonData({'Rarity': rarity, 'EvolvesInto': [1] if canEvolve else []})
  AddExperience(simPokemon, simData, exp)
  return simPokemon.Level - currLevel

#endregion

#region Fights

def WildFight(attack: PokemonData, defend: PokemonData, attackLevel: int, defendLevel: int):
  healthLost: list[int] = [1,3,5,7,10,13,15]
  battleResult = TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult >= 2
  doubleDis = battleResult <= -2
  attackGroup = RarityGroup(attack)
  defendGroup = RarityGroup(defend)
  levelAdvantage = 2 if attackLevel > (defendLevel*2) else 1 if attackLevel > (defendLevel*1.5) else 0
  levelDisadvantage = 2 if defendLevel > (attackLevel*2) else 1 if defendLevel > (attackLevel*1.5) else 0
  if attackLevel < 10 and defendLevel < 10:
    levelAdvantage = 1 if attackLevel > (defendLevel + 3) else 0 
    levelDisadvantage = 1 if defendLevel > (attackLevel + 3) else 0 
  
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

def GymFight(attack: PokemonData, defend: PokemonData, attackLevel: int, gymID: int):
  battleResult = TypeMatch(attack.Types, defend.Types)
  attackGroup = RarityGroup(attack)
  attackGroup = attackGroup % 7 if attackGroup < 10 else attackGroup
  defendGroup = RarityGroup(defend)
  defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
  defendLevel = 100 if gymID >= 1000 else 15 if defendGroup == 1 else 25 if defendGroup == 2 else 35 if defendGroup == 3 else 100
  doubleAdv = battleResult >= 2 or (battleResult > 0 and attackLevel > defendLevel*1.5 and attackGroup >= defendGroup)

  if IsSpecialPokemon(defend) and len(attack.Types) == 1:
    return battleResult >= 1 and attackGroup >= defendGroup

  return doubleAdv and (attackGroup >= defendGroup or (attackGroup == defendGroup-1 and attackLevel > defendLevel*1.25))

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

def RarityGroup(pokemon: PokemonData):
  rarityGroup = 1 if pokemon.Rarity <= 2 else 2 if pokemon.Rarity == 3 else 3
  if IsSpecialPokemon(pokemon):
    rarityGroup = pokemon.Rarity
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

