from dataaccess.utility.jsonreader import GetJson

from models.Pokemon import PokemonData

pokemonFile = "collections/pokemon.json"


def GetAllPokemon():
  pokemon = GetJson(pokemonFile)
  return [PokemonData(x) for x in pokemon]


def GetPokemonByType(type):
  pokemon = GetJson(pokemonFile)
  return [PokemonData(x) for x in pokemon if type.lower() in [y.lower() for y in x['Types']]]


def GetPokemonByProperty(searchVals: list, property: str):
  pokemon = GetJson(pokemonFile)
  return [PokemonData(x) for x in pokemon if searchVals.__contains__(x[property])]


def GetUniquePokemonProperty(prop):
  pokemon = GetJson(pokemonFile)
  return set([x[prop] for x in pokemon])
