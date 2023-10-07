from flask import json

from models.Item import Pokeball, Potion

itemFile = "collections/items.json"


def GetPokeballById(id):
  json = GetJson()
  return next((Pokeball(p) for p in json["Pokeball"] if p['Id'] == id), None)


def GetAllPokeballs():
  json = GetJson()
  return [Pokeball(p) for p in json["Pokeball"]]


def GetPotionById(id):
  json = GetJson()
  return next((Potion(p) for p in json["Potion"] if p['Id'] == id), None)


def GetAllPotions():
  json = GetJson()
  return [Potion(p) for p in json["Potion"]]


def GetJson():
  with open(itemFile) as f:
    return json.load(f)
