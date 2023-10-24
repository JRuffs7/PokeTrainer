import math
import random
from typing import List

from services import typeservice
from dataaccess import pokemonda
from globals import ShinyOdds, StarterDexIds
from models.Pokemon import Pokemon, SpawnPokemon


def GetPokemonCount():
  return pokemonda.GetPokemonCount()


def GetPokemonColors():
  return pokemonda.GetAllColors()


def GetRandomSpawnPokemon():
  count = 0
  pokemon = None
  encounter = random.randint(1, 100)
  while not pokemon:
    pokemonList = GetPokemonByRarity(
        1 if 1 <= encounter <= 60 else 2 if 61 <= encounter <= 80 else
        3 if 81 <= encounter <= 95 else 4 if 96 <= encounter <= 98 else 5)
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
      'IsFemale': female
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


def ConvertSpawnPokemonToPokemon(pokeList: List[SpawnPokemon]):
  return pokemonda.GetPokemonByIds([x.Pokemon_Id for x in pokeList])


def PokemonFight(attack: Pokemon, defend: Pokemon, isGym: bool):
  fightTotal = typeservice.TypeWeakness(attack.Types[0], defend.Types[0])
  fightTotal += typeservice.TypeWeakness(
    attack.Types[1] if len(attack.Types) > 1 else attack.Types[0],
    defend.Types[1] if len(defend.Types) > 1 else defend.Types[0])
  doubleAdv = fightTotal == 2
  doubleDis = fightTotal <= -2
  attackGroup = 1 if attack.Rarity <= 2 else 2 if attack.Rarity == 3 else 3
  defendGroup = 1 if defend.Rarity <= 2 else 2 if defend.Rarity == 3 else 3

  # 1/2 vs 4/5
  if (attackGroup == 1 and defendGroup == 3) or (defendGroup == 1 and attackGroup == 3):
    fightTotal += (2 * (attack.Rarity - defend.Rarity))
  # 1/2 vs 3
  elif (attackGroup == 1 and defendGroup == 2 and not doubleAdv) or (defendGroup == 1 and attackGroup == 2 and not doubleDis):
    fightTotal += (2 * (attack.Rarity - defend.Rarity))
  # 3 vs 4/5
  elif (attackGroup == 2 and defendGroup == 3 and not doubleAdv) or (defendGroup == 2 and attackGroup == 3 and not doubleDis):
    fightTotal += (2 * (attack.Rarity - defend.Rarity))

  #gym battles must use similar rarity
  if isGym and attackGroup < defendGroup:
    fightTotal = -1

  return fightTotal
