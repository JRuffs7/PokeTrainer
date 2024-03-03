import math
import random
from typing import List
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


def GetPokemonImage(pokemon: Pokemon):
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
      'Level': level if level else 1 if pokemon.Rarity <= 2 else 20 if pokemon.Rarity == 3 else 30 if pokemon.Rarity == 4 else 35,
      'CurrentExp': 0
  })

#endregion

#region Trainer Pokemon

def AddExperience(trainerPokemon: Pokemon, trainerRarity: int, exp: int):
  trainerPokemon.CurrentExp += exp
  if trainerPokemon.CurrentExp >= ((50 * trainerRarity) if trainerRarity <= 3 else 250):
    trainerPokemon.Level += 1
    trainerPokemon.CurrentExp -= ((50 * trainerRarity) if trainerRarity <= 3 else 250)


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


def PokemonFight(attack: PokemonData, defend: PokemonData, gymBattle: bool = False):
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

def GetPokemonByRarity(rarity: int):
  return pokemonda.GetPokemonByProperty([rarity], 'Rarity')

