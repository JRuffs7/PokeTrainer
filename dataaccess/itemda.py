from flask import json

from models.Item import Pokeball, Potion

itemFile = "collections/items.json"


def GetAllPokeballs():
  json = GetJson()
  return [Pokeball(p) for p in json["Pokeball"]]


def GetAllPotions():
  json = GetJson()
  return [Potion(p) for p in json["Potion"]]


def GetJson():
  with open(itemFile) as f:
    return json.load(f)
