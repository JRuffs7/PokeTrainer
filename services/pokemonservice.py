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
  doubleType = [x for x in pokeList if len(x.Types) == 2]
  singleType.sort(lambda x: x.Name)
  doubleType.sort(lambda x: (x.Type[0].lower() == type, x.Name))
  return singleType+doubleType


def ConvertSpawnPokemonToPokemon(pokeList: List[SpawnPokemon]):
  return pokemonda.GetPokemonByIds([x.Pokemon_Id for x in pokeList])


def CanTrainerPokemonEvolve(pkmn: SpawnPokemon):
  poke = GetPokemonById(pkmn.Pokemon_Id)
  if poke.Rarity == 1 and len(poke.EvolvesInto) > 1:
    return pkmn.Level >= 20
  elif poke.Rarity == 2 and len(poke.EvolvesInto) > 1:
    return pkmn.Level >= 30
  elif poke.Rarity == 3 and len(poke.EvolvesInto) > 1:
    return pkmn.Level >= 35
  return False


def SplitPokemonForSearch(pokemonId):
  pkmn = GetPokemonById(pokemonId)
  if not Pokemon:
    return None
  
  return [
    PokedexEntry({
        'Name': pkmn.Name,
        'PokedexId': pkmn.PokedexId,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(False, pkmn.FemaleChance == 8),
        'Rarity': pkmn.Rarity,
        'Pokemon': to_dict(SpawnPokemon({
          'Id': '',
          'Pokemon_Id': pkmn.Id,
          'Height': pkmn.Height,
          'Weight': pkmn.Weight,
          'IsShiny': False,
          'IsFemale': pkmn.FemaleChance == 8,
          'Level': None,
          'CurrentExp': None,
          'EvolutionStage': 1 if pkmn.Rarity <= 2 and len(pkmn.EvolvesInto) > 0 else 2 if pkmn.Rarity == 3 and len(pkmn.EvolvesInto) > 0 else 3 if pkmn.Rarity >= 4 else None
        }))
    }),
    PokedexEntry({
        'Name': pkmn.Name,
        'PokedexId': pkmn.PokedexId,
        'Types': pkmn.Types,
        'Sprite': pkmn.GetImage(True, pkmn.FemaleChance == 8),
        'Rarity': pkmn.Rarity,
        'Pokemon': to_dict(SpawnPokemon({
          'Id': '',
          'Pokemon_Id': pkmn.Id,
          'Height': pkmn.Height,
          'Weight': pkmn.Weight,
          'IsShiny': True,
          'IsFemale': pkmn.FemaleChance == 8,
          'Level': None,
          'CurrentExp': None,
          'EvolutionStage': 1 if pkmn.Rarity <= 2 and len(pkmn.EvolvesInto) > 0 else 2 if pkmn.Rarity == 3 and len(pkmn.EvolvesInto) > 0 else 3 if pkmn.Rarity >= 4 else None
        }))
    })
  ]


def PokemonFight(attack: Pokemon, defend: Pokemon):
  fightTotal = typeservice.TypeWeakness(attack.Types[0], defend.Types[0])
  fightTotal += typeservice.TypeWeakness(
    attack.Types[1] if len(attack.Types) > 1 else attack.Types[0],
    defend.Types[1] if len(defend.Types) > 1 else defend.Types[0])
  doubleAdv = fightTotal == 2
  doubleDis = fightTotal <= -2
  attackGroup = 1 if attack.Rarity <= 2 else 2 if attack.Rarity == 3 else 3
  defendGroup = 1 if defend.Rarity <= 2 else 2 if defend.Rarity == 3 else 3

  # 1v2 2v3
  if abs(attackGroup - defendGroup) == 1:
    if (attackGroup < defendGroup and not doubleAdv) or not doubleDis:
      fightTotal += (2 * (attack.Rarity - defend.Rarity))
  # 1v3
  elif abs(attackGroup - defendGroup) == 2:
    fightTotal += (2 * (attack.Rarity - defend.Rarity))

  return fightTotal
