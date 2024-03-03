from typing import List

from flask import json

from models.Pokemon import PokemonData

pokemonFile = "collections/pokemon.json"

def TestMethod(id: int):
  with open(pokemonFile, 'r') as data:
    json_data = data.read()
  jsonData: list[PokemonData] = json.loads(json_data, object_hook=list[PokemonData])
  return next(p for p in jsonData if p.Id == id)

def GetAllPokemon():
  return [
    PokemonData(x) for x in GetJson()
  ]


def GetPokemonCount():
  return {x['PokedexId']: PokemonData(x) for x in GetJson()}.values().__len__()


def GetFormsCount():
  return GetJson().__len__()


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


def GetPokemonByIds(idList: List[int]):
  returnList = []
  for val in idList:
    returnList.append(
        next((PokemonData(p) for p in GetJson() if p['Id'] == val), None))
  return returnList


def GetJson():
  with open(pokemonFile, encoding="utf-8") as f:
    return json.load(f)
