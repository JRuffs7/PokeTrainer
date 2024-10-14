from dataaccess.utility.jsonreader import GetJson

from models.Item import Candy, Item, Pokeball, Potion

itemFile = "collections/items.json"


def GetAllItems():
  items = GetJson(itemFile)
  return [Pokeball(i) if 'CaptureRate' in i else Potion(i) if 'HealingAmount' in i else Candy(i) if 'Experience' in i else Item(i) for i in items if i['Id']]


def GetAllPokeballs():
  pokeballs = GetJson(itemFile)
  return [Pokeball(p) for p in pokeballs if 'CaptureRate' in p]


def GetAllPotions():
  potions = GetJson(itemFile)
  return [Potion(p) for p in potions if 'HealingAmount' in p]


def GetAllCandies():
  candy = GetJson(itemFile)
  return [Candy(c) for c in candy if 'Experience' in c]


def GetAllEvoItems():
  evo = GetJson(itemFile)
  return [Item(e) for e in evo if e['EvolutionItem']]