from dataaccess.utility.jsonreader import GetJson

from models.Pokemon import PokemonData

pokemonFile = "collections/pokemon.json"


def GetAllPokemon():
  return [
    PokemonData(x) for x in GetJson(pokemonFile)
  ]


def GetPokemonByType(type):
  return [
    PokemonData(x) for x in GetJson(pokemonFile) if type.lower() in [y.lower() for y in x['Types']]
  ]


def GetPokemonByProperty(searchVals: list, property: str):
  return [
      PokemonData(x) for x in GetJson(pokemonFile) if searchVals.__contains__(x[property])
  ]


def GetUniquePokemonProperty(prop):
  return set([x[prop] for x in GetJson(pokemonFile)])
