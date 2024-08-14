from dataaccess.utility.jsonreader import GetJson

from models.Item import Candy, Item, Pokeball, Potion

itemFile = "collections/items.json"


def GetAllItems():
  items = GetJson(itemFile)
  retList: list[Item] = []
  for i in items:
    retList.append(Pokeball(i) if 'CaptureRate' in i else Potion(i) if 'HealingAmount' in i else Candy(i) if 'Experience' in i else Item(i))
  return retList


def GetAllPokeballs():
  pokeballs = GetJson(itemFile)["Pokeball"]
  return [Pokeball(p) for p in pokeballs]


def GetAllPotions():
  potions = GetJson(itemFile)["Potion"]
  return [Potion(p) for p in potions]


def GetAllCandies():
  candy = GetJson(itemFile)["Candy"]
  return [Candy(c) for c in candy]