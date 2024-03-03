from typing import List

from flask import json

from models.Pokemon import PokemonData

pokemonFile = "collections/pokemon.json"


def GetAllPokemon():
  return [
    PokemonData(x) for x in GetJson()
  ]


def GetPokemonByType(type):
  return [
    PokemonData(x) for x in GetJson() if type.lower() in [y.lower() for y in x['Types']]
  ]


def GetPokemonByProperty(searchVals: List, property: str):
  return [
      PokemonData(x) for x in GetJson() if searchVals.__contains__(x[property])
  ]


def GetUniquePokemonProperty(prop):
  return set([x[prop] for x in GetJson()])


def GetJson():
  with open(pokemonFile, encoding="utf-8") as f:
    return json.load(f)
