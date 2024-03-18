from dataaccess.utility.jsonreader import GetJson

from models.Item import Candy, Pokeball, Potion

itemFile = "collections/items.json"


def GetAllPokeballs():
  json = GetJson(itemFile)
  return [Pokeball(p) for p in json["Pokeball"]]


def GetAllPotions():
  json = GetJson(itemFile)
  return [Potion(p) for p in json["Potion"]]


def GetAllCandies():
  json = GetJson(itemFile)
  return [Candy(c) for c in json["Candy"]]