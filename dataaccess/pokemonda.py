from typing import List

from flask import json

from models.Pokemon import Pokemon

pokemonFile = "collections/pokemon.json"


def GetPokemonCount():
  return {x['PokedexId']: Pokemon(x) for x in GetJson()}.values().__len__()


def GetFormsCount():
  return GetJson().__len__()


def GetAllColors():
  return set([x['Color'] for x in GetJson()])


def GetPokemonByProperty(searchVals: List, property: str):
  return [
      Pokemon(x) for x in GetJson() if searchVals.__contains__(x[property])
  ]


def GetPokemonByIds(idList: List[int]):
  returnList = []
  for val in idList:
    returnList.append(
        next((Pokemon(p) for p in GetJson() if p['Id'] == val), None))
  return returnList


def GetJson():
  with open(pokemonFile, encoding="utf-8") as f:
    return json.load(f)
