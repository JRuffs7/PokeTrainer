import math
import random
from typing import List

from services import typeservice
from dataaccess import pokemonda
from globals import ShinyOdds, StarterDexIds, to_dict
from models.Pokemon import Pokemon, SpawnPokemon, PokedexEntry


def GetAllPokemon():
  return pokemonda.GetAllPokemon()


def GetPokemonCount():
  return pokemonda.GetPokemonCount()


def GetPokemonColors():
  return pokemonda.GetUniquePokemonProperty('Color')


def GetPokemonTypes():
  types = pokemonda.GetUniquePokemonProperty('Type')


def GetRandomSpawnPokemon():
  count = 0
  pokemon = None
  encounter = random.randint(1, 100)
  while not pokemon:
    pokemonList = GetPokemonByRarity(
        1 if 1 <= encounter <= 60 else 2 if 61 <= encounter <= 85 else
        3 if 86 <= encounter <= 95 else 4 if 96 <= encounter <= 98 else 5)
    pokemon = random.choice(pokemonList)
    if pokemon.IsMega or pokemon.IsBattleOnly or pokemon.IsLegendary or pokemon.IsMythical or not pokemon.Sprite or not pokemon.ShinySprite:
      pokemon = None

    for range in StarterDexIds:
      if pokemon and pokemon.PokedexId in range:
        pokemon = None
        break

    count += 1
    if count == 21:
      raise Exception("Too many pokemon tries")

  return GenerateSpawnPokemon(pokemon)


def GenerateSpawnPokemon(pokemon: Pokemon):
  shiny = random.randint(0, ShinyOdds) == int(ShinyOdds / 2)
  height = round(
      random.uniform(math.floor(
          (pokemon.Height * 0.9)), math.ceil((pokemon.Height * 1.1))) / 10, 2)
  weight = round(
      random.uniform(math.floor(
          (pokemon.Weight * 0.9)), math.ceil((pokemon.Weight * 1.1))) / 10, 2)
  female = random.randint(0, 100) < int(pokemon.FemaleChance / 8 *
                                        100) if pokemon.FemaleChance else None
  return SpawnPokemon({
      'Pokemon_Id': pokemon.Id,
      'Height': height if height > 0.00 else 0.01,
      'Weight': weight if weight > 0.00 else 0.01,
      'IsShiny': shiny,
      'IsFemale': female,
      'Level': 1 if pokemon.Rarity <= 2 else 20 if pokemon.Rarity == 3 else 30 if pokemon.Rarity == 4 else 35,
      'CurrentExp': 0
  })


def GetPokemonById(id: int):
  results = pokemonda.GetPokemonByProperty([id], 'Id')
  if results:
    return results.pop()
  return None


def GetPokemonByRarity(rarity: int):
  return pokemonda.GetPokemonByProperty([rarity], 'Rarity')


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

  return [PokedexEntry({ 'Name': f"{p.Name} ({','.join(p.Types)})"}) for p in singleType]+[PokedexEntry({ 'Name': f"{p.Name} ({','.join(p.Types)})"}) for p in firstType]+[PokedexEntry({ 'Name': f"{p.Name} ({','.join(p.Types)})"}) for p in secondType]


def ConvertSpawnPokemonToPokedexEntry(pokemon: SpawnPokemon):
  pkmn = GetPokemonById(pokemon.Pokemon_Id)
  return PokedexEntry({
      'Id': pokemon.Id,
      'Name': pkmn.Name,
      'PokedexId': pkmn.PokedexId,
      'Types': pkmn.Types,
      'Sprite': pkmn.GetImage(pokemon.IsShiny, pokemon.IsFemale),
      'Rarity': pkmn.Rarity,
      'Level': 1 if pkmn.Rarity <= 2 else 20 if pkmn.Rarity == 3 else 30 if pkmn.Rarity == 4 else 35,
      'CurrentExp': 0,
      'Pokemon': pokemon.__dict__
    })


def ConvertSpawnPokemonToPokemon(pokeList: List[SpawnPokemon]):
  return pokemonda.GetPokemonByIds([x.Pokemon_Id for x in pokeList])


def CanTrainerPokemonEvolve(pkmn: PokedexEntry):
  poke = GetPokemonById(pkmn.Pokemon.Pokemon_Id)
  if pkmn.Rarity == 1 and len(poke.EvolvesInto) >= 1:
    return pkmn.Level >= 20
  elif pkmn.Rarity == 2 and len(poke.EvolvesInto) >= 1:
    return pkmn.Level >= 30
  elif pkmn.Rarity == 3 and len(poke.EvolvesInto) >= 1:
    return pkmn.Level >= 35
  return False


def SplitPokemonForSearch(pokemonId):
  pkmn = GetPokemonById(pokemonId)
  if not pkmn:
    return None
  pkmnList = []
  pkmnList.append(PokedexEntry({
      'Name': pkmn.Name,
      'Types': pkmn.Types,
      'Sprite': pkmn.GetImage(False, pkmn.FemaleChance == 8),
      'Rarity': pkmn.Rarity,
      'Pokemon': to_dict(SpawnPokemon({
        'Height': pkmn.Height,
        'Weight': pkmn.Weight,
        'IsShiny': False,
        'IsFemale': pkmn.FemaleChance == 8,
      }))
  }))
  if pkmn.ShinySprite:
    pkmnList.append(PokedexEntry({
        'Name': pkmn.Name,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(True, pkmn.FemaleChance == 8),
        'Rarity': pkmn.Rarity,
        'Pokemon': to_dict(SpawnPokemon({
          'Height': pkmn.Height,
          'Weight': pkmn.Weight,
          'IsShiny': True,
          'IsFemale': pkmn.FemaleChance == 8,
        }))
    }))
  if pkmn.SpriteFemale and pkmn.FemaleChance != 0:
    pkmnList.append(PokedexEntry({
        'Name': pkmn.Name,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(False, True),
        'Rarity': pkmn.Rarity,
        'Pokemon': to_dict(SpawnPokemon({
          'Height': pkmn.Height,
          'Weight': pkmn.Weight,
          'IsShiny': False,
          'IsFemale': True,
        }))
    }))
  if pkmn.ShinySpriteFemale and pkmn.FemaleChance != 0:
    pkmnList.append(PokedexEntry({
        'Name': pkmn.Name,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(True, True),
        'Rarity': pkmn.Rarity,
        'Pokemon': to_dict(SpawnPokemon({
          'Height': pkmn.Height,
          'Weight': pkmn.Weight,
          'IsShiny': True,
          'IsFemale': True,
        }))
    }))
  return pkmnList


def EvolvePokemon(initial: PokedexEntry, evolveId):
  pkmn = GetPokemonById(evolveId)
  spawn = GenerateSpawnPokemon(pkmn)
  spawn.IsFemale = initial.Pokemon.IsFemale
  spawn.IsShiny = initial.Pokemon.IsShiny
  return PokedexEntry({
      'Id': initial.Id,
      'Name': pkmn.Name,
      'PokedexId': pkmn.PokedexId,
      'Types': pkmn.Types,
      'Sprite': pkmn.GetImage(spawn.IsShiny, spawn.IsFemale),
      'Rarity': pkmn.Rarity,
      'Level': initial.Level,
      'CurrentExp': initial.CurrentExp,
      'Pokemon': spawn.__dict__
    })


def PokemonFight(attack: Pokemon, defend: Pokemon, gymBattle: bool = False):
  try:
    fightTotal = typeservice.TypeWeakness(attack.Types[0].lower(), defend.Types[0].lower())
    fightTotal += typeservice.TypeWeakness(
      attack.Types[1].lower() if len(attack.Types) > 1 else attack.Types[0].lower(),
      defend.Types[1].lower() if len(defend.Types) > 1 else defend.Types[0].lower())
    doubleAdv = fightTotal == 2
    doubleDis = fightTotal <= -2
    attackGroup = 1 if attack.Rarity <= 2 else 2 if attack.Rarity == 3 else 3
    defendGroup = 1 if defend.Rarity <= 2 else 2 if defend.Rarity == 3 else 3

    if gymBattle:
      return 1 if doubleAdv and attackGroup >= defendGroup else 0

    # 1v2 2v3
    if abs(attackGroup - defendGroup) == 1:
      if (attackGroup < defendGroup and not doubleAdv) or not doubleDis:
        fightTotal += (2 * (attack.Rarity - defend.Rarity))
    # 1v3
    elif abs(attackGroup - defendGroup) == 2:
      fightTotal += (2 * (attack.Rarity - defend.Rarity))

    return fightTotal
  except Exception as e:
    print(f"{e}")
