import math
import uuid
from math import ceil, floor
from random import choice, uniform
from models.Item import Item, Pokeball, Potion
from models.Stat import StatEnum
from models.Trainer import Trainer
from models.Zone import Zone
from models.enums import SpecialSpawn

from services import battleservice, moveservice, statservice, trainerservice
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

def GetStarterPokemon():
  return [p for p in pokemonda.GetAllPokemon() if p.IsStarter]

def GetEvolutionLine(pokemonId: int, pokemonData: list[PokemonData] | None):
  pokemon = pokemonda.GetAllPokemon() if not pokemonData else pokemonData
  idArray: list[int] = [pokemonId]
  preEvo = next((p for p in pokemon if pokemonId in [e.EvolveID for e in p.EvolvesInto]), None)
  while preEvo is not None:
    idArray.append(preEvo.Id)
    preEvo = next((p for p in pokemon if preEvo.Id in [e.EvolveID for e in p.EvolvesInto]), None)
  return idArray

def IsLegendaryPokemon(pokemon: PokemonData):
  return pokemon.IsLegendary or pokemon.IsMythical or pokemon.IsUltraBeast

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


def GetOwnedPokemonDescription(pokemon: Pokemon, pkmnData: PokemonData = None):
  pkmn = GetPokemonById(pokemon.Pokemon_Id) if not pkmnData else pkmnData
  return f"Lvl. {pokemon.Level} ({pokemon.CurrentExp}/{NeededExperience(pokemon, pkmn)}xp | H:{pokemon.Height} | W:{pokemon.Weight} | Types: {'/'.join([statservice.GetType(t).Name for t in pkmn.Types])}"

def GetBattlePokemonDescription(pokemon: Pokemon, pkmnData: PokemonData = None):
  pkmn = GetPokemonById(pokemon.Pokemon_Id) if not pkmnData else pkmnData
  return f"Lvl {pokemon.Level} | HP: {pokemon.CurrentHP}/{statservice.GenerateStat(pokemon, pkmnData, StatEnum.HP)} | Types: {'/'.join([statservice.GetType(t).Name for t in pkmn.Types])} | Ailment: {statservice.GetAilment(pokemon.CurrentAilment).Name.upper() if pokemon.CurrentAilment else ' - '}"


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

def ExpForPokemon(pokemon: Pokemon, data: PokemonData, expShare: bool, victorLevel: int):
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
  return round(part4*t*e*v*f*p)





def SpawnPokemon(specialZone: Zone|None, badgeBonus: int, shinyOdds: int):
  pokemonList = pokemonda.GetPokemonByProperty([1, 2, 3], 'Rarity')
  if specialZone:
    pokemonList = [p for p in pokemonList if len(set(specialZone.Types).intersection(set(p.Types))) > 0]
  pokemon = None
  while not pokemon:
    pokemon = choice(pokemonList)
    if not CanSpawn(pokemon):
      pokemon = None

  spawn = GenerateSpawnPokemon(pokemon, shinyOdds)
  spawn.Level += floor(badgeBonus/2)
  return spawn

def GetSpecialSpawn():
  spawnType = choice(list(SpecialSpawn))
  pokemonList = pokemonda.GetPokemonByProperty([True], spawnType.value)
  pkmn = None
  while not pkmn:
    pkmn = choice(pokemonList)
    if pkmn.IsFossil and not pkmn.EvolvesInto:
      pkmn = None
  return GenerateSpawnPokemon(pkmn, level=5 if pkmn.IsStarter or pkmn.IsFossil else 75 if pkmn.IsLegendary or pkmn.IsMythical else 40)

def GenerateSpawnPokemon(pokemon: PokemonData, shinyOdds: int = ShinyOdds, level: int | None = None):
  shiny = choice(range(0, shinyOdds)) == int(shinyOdds / 2)
  height = round(
      uniform((pokemon.Height * 0.9), (pokemon.Height * 1.1)) / 10, 2)
  weight = round(
      uniform((pokemon.Weight * 0.9), (pokemon.Weight * 1.1)) / 10, 2)
  female = choice(range(0, 100)) < int(pokemon.FemaleChance / 8 * 100) if pokemon.FemaleChance >= 0 else None
  spawn = Pokemon.from_dict({
      'Id': uuid.uuid4().hex,
      'Pokemon_Id': pokemon.Id,
      'Height': height if height > 0.00 else 0.01,
      'Weight': weight if weight > 0.00 else 0.01,
      'IsShiny': shiny,
      'IsFemale': female,
      'Level': level if level else choice(range(3,8)) if pokemon.Rarity <= 2 else choice(range(20,26)) if pokemon.Rarity == 3 else choice(range(30,36)),
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

def PokeCenter(trainer: Trainer, team: list[Pokemon]):
  trainer.Money = max(trainer.Money - 500, 0)
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
    expNeeded = NeededExperience(trainerPokemon, pkmnData)

  if trainerPokemon.Level == 100:
    trainerPokemon.CurrentExp = 0

def NeededExperience(pokemon: Pokemon, data: PokemonData):
  currLvlExp, nextLvlExp = statservice.ExpCalculator(pokemon, data)
  return nextLvlExp - currLvlExp

def CanPokemonEvolve(pokemon: Pokemon, pkmn: PokemonData, items: list[Item]):
  for evData in pkmn.EvolvesInto:
    if evData.EvolveLevel and pokemon.Level < evData.EvolveLevel:
      continue
    if evData.GenderNeeded and ((evData.GenderNeeded == 1 and not pokemon.IsFemale) or (evData.GenderNeeded == 2 and pokemon.IsFemale)):
      continue
    if evData.ItemNeeded and not next((i for i in items if i.Id == evData.ItemNeeded), None):
      continue
    if evData.MoveNeeded and not next((m for m in pokemon.LearnedMoves if m.MoveId == evData.MoveNeeded), None):
      continue
    return True
  return False

def AvailableEvolutions(pokemon: Pokemon, pkmnData: PokemonData, items: list[Item]):
  evolveIdList: list[int] = []
  for evData in pkmnData.EvolvesInto:
    if evData.EvolveLevel and pokemon.Level < evData.EvolveLevel:
      continue
    if evData.GenderNeeded and ((evData.GenderNeeded == 1 and not pokemon.IsFemale) or (evData.GenderNeeded == 2 and pokemon.IsFemale)):
      continue
    if evData.ItemNeeded and not next((i for i in items if i.Id == evData.ItemNeeded), None):
      continue
    if evData.MoveNeeded and not next((m for m in pokemon.LearnedMoves if m.MoveId == evData.MoveNeeded), None):
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
  currTotalHP = statservice.GenerateStat(initial, initialData)
  spawn = GenerateSpawnPokemon(evolveData)
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
      'LearnedMoves': initial.LearnedMoves,
      'CurrentAilment': initial.CurrentAilment
    })
  evolveTotalHP = statservice.GenerateStat(evolved, evolveData)
  evolved.CurrentHP += (evolveTotalHP - currTotalHP)
  if evolved.CurrentHP > evolveTotalHP:
    evolved.CurrentHP = evolveTotalHP
  return evolved

def GetPokemonThatCanEvolve(trainer: Trainer, ownedPokemon: list[Pokemon]):
  if not ownedPokemon:
    return None
  dataList = GetPokemonByIdList([p.Pokemon_Id for p in ownedPokemon])
  return [p for p in ownedPokemon if CanPokemonEvolve(p, next(pk for pk in dataList if pk.Id == p.Pokemon_Id), trainerservice.GetTrainerItemList(trainer, 3))]

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

def TryUseItem(pokemon: Pokemon, data: PokemonData, potion: Potion):
  used = False
  if pokemon.CurrentHP < statservice.GenerateStat(pokemon, data, StatEnum.HP):
    used = True
    pokemon.CurrentHP = min(pokemon.CurrentHP + (potion.HealingAmount or 1000), statservice.GenerateStat(pokemon, data, StatEnum.HP))

  if pokemon.CurrentAilment and pokemon.CurrentAilment in potion.AilmentCures:
    used = True
    pokemon.CurrentAilment = None
  return used

#endregion
