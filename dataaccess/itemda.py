from dataaccess.utility.jsonreader import GetJson

from models.Item import Candy, Item, Pokeball, Potion

itemFile = "collections/items.json"


def GetAllItems():
  evolutions = GetJson(itemFile)["Evolution"]
  return [Item(p) for p in evolutions]


def GetAllPokeballs():
  pokeballs = GetJson(itemFile)["Pokeball"]
  return [Pokeball(p) for p in pokeballs]


def GetAllPotions():
  potions = GetJson(itemFile)["Potion"]
  return [Potion(p) for p in potions]


def GetAllCandies():
  candy = GetJson(itemFile)["Candy"]
  return [Candy(c) for c in candy]