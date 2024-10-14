import math
import uuid
from math import ceil
from random import choice, uniform
from models.Item import Candy, Item, Pokeball, Potion
from models.Move import MoveData
from models.Stat import StatEnum
from models.Trainer import Trainer
from models.enums import SpecialSpawn

from services import moveservice, statservice, trainerservice
from dataaccess import pokemonda
from globals import FemaleSign, MaleSign, ShinyOdds, ShinySign
from models.Pokemon import Move, PokemonData, Pokemon

#region Data

def GetAllPokemon():
  return pokemonda.GetAllPokemon()

def GetPokemonById(id: int):
  results = pokemonda.GetPokemonByProperty([id], 'Id')
  if results:
    return results.pop()
  return None

def GetPokemonByPokedexId(dexId: int):
  return pokemonda.GetPokemonByProperty([dexId], 'PokedexId')

def GetPokemonByIdList(idList: list[int]):
  return pokemonda.GetPokemonByProperty(idList, 'Id')

def GetPokemonColors():
  return pokemonda.GetUniquePokemonProperty('Color')

def GetPokemonByColor(color: str):
  return pokemonda.GetPokemonByProperty([color], 'Color')

def GetPokemonByType(type: int):
  pokeList = pokemonda.GetPokemonByType(type)
  singleType = [x for x in pokeList if len(x.Types) == 1]
  firstType = [x for x in pokeList if len(x.Types) == 2 and x.Types[0] == type]
  secondType = [x for x in pokeList if len(x.Types) == 2 and x.Types[1] == type]
  singleType.sort(key=lambda x: x.Name)
  firstType.sort(key=lambda x: x.Name)
  secondType.sort(key=lambda x: x.Name)

  return singleType+firstType+secondType

def GetPokemonByRarity(rarity: list[int]):
  return pokemonda.GetPokemonByProperty(rarity, 'Rarity')

def GetPokemonByRegion(region: int):
  return pokemonda.GetPokemonByProperty([region], 'Generation')

def GetStarterPokemon():
  return [p for p in pokemonda.GetAllPokemon() if p.IsStarter]

def GetInitialStage(pokemonId: int):
  pokemon = pokemonda.GetAllPokemon()
  initial = next(p for p in pokemon if p.Id == pokemonId)
  preEvo = next((p for p in pokemon if pokemonId in [e.EvolveID for e in p.EvolvesInto]), None)
  while preEvo is not None:
    initial = preEvo
    preEvo = next((p for p in pokemon if preEvo.Id in [e.EvolveID for e in p.EvolvesInto]), None)
  return initial

def IsLegendaryPokemon(pokemon: PokemonData):
  return pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsUltraBeast or pokemon.IsParadox

def IsSpecialSpawn(pokemon: PokemonData):
  return IsLegendaryPokemon(pokemon) or pokemon.IsParadox or pokemon.IsStarter or (pokemon.IsFossil and pokemon.EvolvesInto)

def GetPreviousStages(pokemon: PokemonData, allPkmn: list[PokemonData] = None):
  if not allPkmn:
    allPkmn = GetAllPokemon()

  return [p for p in allPkmn if [e for e in p.EvolvesInto if e.EvolveID == pokemon.Id]]

def GetShopValue(pokemon: PokemonData):
  if IsLegendaryPokemon(pokemon):
    return 100000
  elif pokemon.IsParadox:
    return 75000
  elif IsSpecialSpawn(pokemon):
    return 50000
  elif pokemon.Rarity <= 2:
    return 15000
  elif pokemon.Rarity == 3 and not pokemon.EvolvesInto:
    return 25000
  #elif pokemon.Rarity <= 10:
  return None

#endregion

#region Display

def GetPokemonDisplayName(pokemon: Pokemon, pkmn: PokemonData = None, showGender: bool = True, showShiny: bool = True):
  if not pokemon.Nickname:
    data = GetPokemonById(pokemon.Pokemon_Id) if not pkmn else pkmn
    name = data.Name
  else:
    name = pokemon.Nickname
  genderEmoji = f"{f' {FemaleSign}' if pokemon.IsFemale == True else f' {MaleSign}' if pokemon.IsFemale == False else ''}" if showGender else ""
  shinyEmoji = f"{f'{ShinySign}' if pokemon.IsShiny else ''}" if showShiny else ""
  return f"{name}{genderEmoji}{shinyEmoji}"

def GetPokemonDescription(pokemon: Pokemon, pkmnData: PokemonData = None, descType: int = 0):
  data = GetPokemonById(pokemon.Pokemon_Id) if not pkmnData else pkmnData
  match descType:
    case 1: #Experience
      return f"Lvl. {pokemon.Level} | XP: {pokemon.CurrentExp}/{NeededExperience(pokemon, data)}"
    case 2: #Potion
      return f"Lvl. {pokemon.Level} | HP: {pokemon.CurrentHP}/{statservice.GenerateStat(pokemon, data, StatEnum.HP)} | Ailment: {pokemon.CurrentAilment}"
    case 3: #Battle
      return f"Lvl {pokemon.Level} | HP: {pokemon.CurrentHP}/{statservice.GenerateStat(pokemon, pkmnData, StatEnum.HP)} | Types: {'/'.join([statservice.GetType(t).Name for t in data.Types])} | Ailment: {statservice.GetAilment(pokemon.CurrentAilment).Name.upper() if pokemon.CurrentAilment else ' - '}"
    case _:
      return f"Lvl. {pokemon.Level} | H:{pokemon.Height} | W:{pokemon.Weight} | Types: {'/'.join([statservice.GetType(t).Name for t in data.Types])}"

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

def ExpForPokemon(pokemon: Pokemon, data: PokemonData, isWild: bool, expShare: bool, victorLevel: int):
  a = 1 if isWild else 1.5
  b = data.BaseDefeatExp
  L = pokemon.Level
  s = 1 if not expShare else 2
  Lp = victorLevel
  t = 1
  e = 1
  v = 1
  f = 1
  p = 1

  part1 = (b*L)/5
  part2 = 1/s
  part3 = math.pow((((2*L) + 10)/(L + Lp + 10)),2.5)
  part4 = (part1*part2*part3) + 1
  return round(part4*a*t*e*v*f*p)

def SpawnPokemon(region: int, badgesInRegion: int, shinyOdds: int):
  encounterRng = choice(range(100))
  spawnChance = (
    4 if encounterRng%2 == 0 else 
    3 if encounterRng < 60 else
    2 if encounterRng < 97 else 
    1 if badgesInRegion > 6 else 4
    )

  pokemonList = [p for p in pokemonda.GetPokemonByProperty([1,2] if badgesInRegion < 3 else [1,2,3], 'Rarity') if p.Generation == region and p.EncounterChance == spawnChance]
  while not pokemonList and spawnChance < 4:
    spawnChance += 1
    pokemonList = [p for p in pokemonda.GetPokemonByProperty([1,2] if badgesInRegion < 3 else [1,2,3], 'Rarity') if p.Generation == region and p.EncounterChance == spawnChance]
  if not pokemonList:
    return None,None
  
  pokemon = None
  while not pokemon:
    pokemon = choice(pokemonList)
    if not CanSpawn(pokemon, pokemonList):
      pokemon = None

  range1 = 2 + (5*badgesInRegion)
  range2 = 10 + (5*badgesInRegion)
  level = choice(range(range1, range2))
  spawn = GenerateSpawnPokemon(pokemon, level, shinyOdds)
  evos = AvailableEvolutions(spawn, pokemon, [])
  if evos and spawn.Level >= 20 and choice(range(100)) < 30:
    evData = GetPokemonById(choice(evos))
    spawn = EvolvePokemon(spawn, pokemon, evData)
    spawn.CurrentHP = statservice.GenerateStat(spawn, evData, StatEnum.HP)
  return (spawn,choice(range(100)) < 1)

def SpawnLegendary(region: int, shinyOdds: int, ownedList: list[int]):
  pokemonList = [p for p in pokemonda.GetAllPokemon() if p.Generation == region and IsLegendaryPokemon(p) and p.Id not in ownedList]
  if not pokemonList:
    return None
  evolveList = []
  for p in pokemonList:
    if p.EvolvesInto:
      evolveList.extend([e.EvolveID for e in p.EvolvesInto])
  pokemon = None
  while not pokemon:
    pokemon = choice(pokemonList)
    if pokemon.Id in evolveList:
      pokemon = None

  level = 50 if pokemon.IsMythical or pokemon.IsParadox or pokemon.Rarity < 10 else 60 if pokemon.IsUltraBeast else 75
  spawn = GenerateSpawnPokemon(pokemon, level, shinyOdds)
  return spawn

def GetLegendaryInRegion(region: int):
  return [p for p in pokemonda.GetAllPokemon() if p.Generation == region and IsLegendaryPokemon(p)]

def GetSpecialSpawn():
  spawnType = choice(list(SpecialSpawn))
  pokemonList = pokemonda.GetPokemonByProperty([True], spawnType.value)
  pkmn = None
  while not pkmn:
    pkmn = choice(pokemonList)
    if pkmn.IsFossil and not pkmn.EvolvesInto:
      pkmn = None
  return GenerateSpawnPokemon(pkmn, 5 if pkmn.IsStarter or pkmn.IsFossil else 75 if pkmn.IsLegendary or pkmn.IsMythical else 40)

def GenerateSpawnPokemon(pokemon: PokemonData, level: int, shinyOdds: int = ShinyOdds):
  isshiny = (choice(range(0, shinyOdds)) == int(shinyOdds / 2)) if shinyOdds > 0 else False
  height = round(uniform((pokemon.Height * 0.9), (pokemon.Height * 1.1)) / 10, 2)
  weight = round(uniform((pokemon.Weight * 0.9), (pokemon.Weight * 1.1)) / 10, 2)
  isfemale = choice(range(0, 100)) < int(pokemon.FemaleChance / 8 * 100) if pokemon.FemaleChance != None and pokemon.FemaleChance >= 0 else None
  spawn = Pokemon.from_dict({
      'Id': uuid.uuid4().hex,
      'Pokemon_Id': pokemon.Id,
      'Height': max(height, 0.01),
      'Weight': max(weight, 0.01),
      'IsShiny': isshiny,
      'IsFemale': isfemale,
      'Level': level,
      'CurrentExp': 0,
      'Nature': choice(statservice.GetAllNatures()).Id,
      'IVs': {
        "1": choice(range(32)),
        "2": choice(range(32)),
        "3": choice(range(32)),
        "4": choice(range(32)),
        "5": choice(range(32)),
        "6": choice(range(32)),
      },
      'CurrentAilment': None
  })
  moves = []
  for move in dict(reversed(sorted(pokemon.LevelUpMoves.items(), key=lambda move: move[1]))):
    if pokemon.LevelUpMoves[move] <= spawn.Level:
      moves.append(int(move))
    if len(moves) == 4:
      break
  spawn.LearnedMoves = [Move({'MoveId': m.Id, 'PP': m.BasePP}) for m in moveservice.GetMovesById(moves)]
  spawn.CurrentHP = statservice.GenerateStat(spawn, pokemon, StatEnum.HP)
  return spawn

def CanSpawn(pokemon: PokemonData, pokemonList: list[PokemonData]):
  if pokemon.Id == 132:
    return False

  if pokemon.IsMega or pokemon.IsUltraBeast or pokemon.IsParadox or pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsFossil:
    return False
  
  if pokemon.Rarity > 3 or (pokemon.Rarity == 3 and pokemon.EvolvesInto):
    return False
  
  if not pokemon.Sprite and not pokemon.ShinySprite:
    return False
  
  for pkmn in [p for p in pokemonList if p.IsStarter]:
    if pkmn.PokedexId <= pokemon.PokedexId <= pkmn.PokedexId+2:
      return False

  return  True

def CaptureSuccess(pokeball: Pokeball, pokemon: PokemonData, level: int):
  if pokeball.Id == 1: #MasterBall
    return True

  randInt = choice(range(1,256))
  if level <= 13:
    calc = ceil(((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)*((36-(2*level))/10))
  else:
    calc = ceil((pokemon.CaptureRate*pokeball.CaptureRate*2)/3)

  return randInt < calc

#endregion

#region Trainer Pokemon

def PokeCenter(team: list[Pokemon]):
  for p in team:
    HealPokemon(p, GetPokemonById(p.Pokemon_Id))

def AddExperience(trainerPokemon: Pokemon, pkmnData: PokemonData, exp: int):
  trainerPokemon.CurrentExp += exp if trainerPokemon.Level < 100 else 0
  expNeeded = NeededExperience(trainerPokemon, pkmnData)
  while trainerPokemon.CurrentExp >= expNeeded and trainerPokemon.Level < 100:
    oldTotalHP = statservice.GenerateStat(trainerPokemon, pkmnData, StatEnum.HP)
    trainerPokemon.Level += 1
    trainerPokemon.CurrentExp -= expNeeded
    newTotalHP = statservice.GenerateStat(trainerPokemon, pkmnData, StatEnum.HP)
    trainerPokemon.CurrentHP = min(trainerPokemon.CurrentHP + (newTotalHP - oldTotalHP), statservice.GenerateStat(trainerPokemon, pkmnData, StatEnum.HP))
    if len(trainerPokemon.LearnedMoves) < 4:
      newMoves = [int(m) for m in pkmnData.LevelUpMoves if (pkmnData.LevelUpMoves[m] == trainerPokemon.Level) and (int(m) not in [mo.MoveId for mo in trainerPokemon.LearnedMoves])]
      if newMoves:
        for n in newMoves:
          if len(trainerPokemon.LearnedMoves) < 4:
            newMove = moveservice.GetMoveById(n)
            trainerPokemon.LearnedMoves.append(Move({'MoveId': newMove.Id, 'PP': newMove.BasePP}))
    expNeeded = NeededExperience(trainerPokemon, pkmnData)

  if trainerPokemon.Level == 100:
    trainerPokemon.CurrentExp = 0

def NeededExperience(pokemon: Pokemon, data: PokemonData):
  currLvlExp, nextLvlExp = statservice.ExpCalculator(pokemon, data)
  return nextLvlExp - currLvlExp

def AvailableEvolutions(pokemon: Pokemon, pkmnData: PokemonData, items: list[Item], spawn: bool = False):
  evolveIdList: list[int] = []
  for evData in pkmnData.EvolvesInto:
    if evData.EvolveLevel and pokemon.Level < evData.EvolveLevel:
      continue
    if evData.GenderNeeded and ((evData.GenderNeeded == 1 and not pokemon.IsFemale) or (evData.GenderNeeded == 2 and pokemon.IsFemale)):
      continue
    if evData.ItemNeeded and not next((i for i in items if i.Id == evData.ItemNeeded), None):
      continue
    if not spawn and evData.MoveNeeded and not next((m for m in pokemon.LearnedMoves if m.MoveId == evData.MoveNeeded), None):
      continue
    evolveIdList.append(evData.EvolveID)
  return evolveIdList

def GetRandomEvolveList(pkmn: PokemonData, evolveIds: list[int]):
  levelEvolves = [p.EvolveID for p in pkmn.EvolvesInto if p.EvolveLevel and p.EvolveID in evolveIds]
  if len(levelEvolves) > 1:
    return levelEvolves
  itemEvolves = [p.EvolveID for p in pkmn.EvolvesInto if p.ItemNeeded and p.EvolveID in evolveIds]
  if len(itemEvolves) > 1:
    return itemEvolves
  moveEvolves = [p.EvolveID for p in pkmn.EvolvesInto if p.MoveNeeded and p.EvolveID in evolveIds]
  if len(moveEvolves) > 1:
    return moveEvolves
  return None

def EvolvePokemon(initial: Pokemon, initialData: PokemonData, evolveData: PokemonData):
  currTotalHP = statservice.GenerateStat(initial, initialData, StatEnum.HP)
  spawn = GenerateSpawnPokemon(evolveData, initial.Level)
  evolved = Pokemon.from_dict({
      'Id': initial.Id,
      'Pokemon_Id': evolveData.Id,
      'Nickname': initial.Nickname,
      'Height': spawn.Height,
      'Weight': spawn.Weight,
      'IsShiny': initial.IsShiny,
      'IsFemale': initial.IsFemale,
      'Level': initial.Level,
      'CurrentExp': initial.CurrentExp,
      'Nature': initial.Nature,
      'IVs': initial.IVs,
      'CurrentAilment': initial.CurrentAilment
    })
  evolveTotalHP = statservice.GenerateStat(evolved, evolveData, StatEnum.HP)
  evolved.CurrentHP += (evolveTotalHP - currTotalHP)
  evolved.LearnedMoves = initial.LearnedMoves
  if evolved.CurrentHP > evolveTotalHP:
    evolved.CurrentHP = evolveTotalHP
  return evolved

def GetPokemonThatCanEvolve(trainer: Trainer):
  trainerTeam = trainerservice.GetTeam(trainer)
  dataList = GetPokemonByIdList([p.Pokemon_Id for p in trainerTeam])
  return [p for p in trainerTeam if AvailableEvolutions(p, next(pk for pk in dataList if pk.Id == p.Pokemon_Id), trainerservice.GetTrainerItemList(trainer))]

def SimulateLevelGain(pokemon: Pokemon, data: PokemonData, exp: int):
  simPokemon = Pokemon.from_dict({'Level': pokemon.Level, 'CurrentExp': pokemon.CurrentExp, 'IVs': pokemon.IVs, 'CurrentHP': pokemon.CurrentHP})
  AddExperience(simPokemon, data, exp)
  return simPokemon.Level

def RarityGroup(pokemon: PokemonData):
  rarityGroup = 1 if pokemon.Rarity <= 2 else 2 if pokemon.Rarity == 3 else 3
  if IsLegendaryPokemon(pokemon):
    rarityGroup = pokemon.Rarity
  return rarityGroup

def HealPokemon(pokemon: Pokemon, data: PokemonData):
  pokemon.CurrentAilment = None
  pokemon.CurrentHP = statservice.GenerateStat(pokemon, data, StatEnum.HP)
  for m in pokemon.LearnedMoves:
    m.PP = moveservice.GetMoveById(m.MoveId).BasePP

def TryUsePotion(pokemon: Pokemon, data: PokemonData, potion: Potion):
  used = False
  if pokemon.CurrentHP < statservice.GenerateStat(pokemon, data, StatEnum.HP):
    used = True
    pokemon.CurrentHP = min(pokemon.CurrentHP + (potion.HealingAmount or 1000), statservice.GenerateStat(pokemon, data, StatEnum.HP))

  if pokemon.CurrentAilment and pokemon.CurrentAilment in potion.AilmentCures:
    used = True
    pokemon.CurrentAilment = None
  return used

def TryUseCandy(pokemon: Pokemon, data: PokemonData, candy: Candy, amount: int):
  num = 0
  if candy.Experience == None:
    while num < amount and pokemon.Level < 100:
      AddExperience(
        pokemon, 
        data, 
        (NeededExperience(pokemon, data) - pokemon.CurrentExp))
      num += 1
  else:
    while num < amount and pokemon.Level < 100:
      nextLevel = NeededExperience(pokemon, data) - pokemon.CurrentExp
      numToNextLvl = ceil(nextLevel/candy.Experience)
      numToUse = min(numToNextLvl, amount, amount - num)
      AddExperience(
        pokemon, 
        data, 
        candy.Experience*numToUse)
      num += numToUse
  return num

def GetAvailableLevelMoves(pokemon: Pokemon, data: PokemonData):
  return [moveservice.GetMoveById(int(m)) for m in data.LevelUpMoves if data.LevelUpMoves[m] <= pokemon.Level and int(m) not in [mo.MoveId for mo in pokemon.LearnedMoves]]

def LearnNewMove(pokemon: Pokemon, newMove: MoveData, oldMove: MoveData|None):
  if (len(pokemon.LearnedMoves) == 4) and (not oldMove):
    return False
  
  if oldMove:
    pokemon.LearnedMoves = [m for m in pokemon.LearnedMoves if m.MoveId != oldMove.Id]
  pokemon.LearnedMoves.append(Move({'MoveId': newMove.Id, 'PP': newMove.BasePP}))
  return True

#endregion
