from random import choice
from dataaccess import eggda, itemda
from models.Item import Candy, Pokeball, Potion


def GetAllItems():
  return itemda.GetAllItems()


def GetAllPokeballs():
  return [i for i in GetAllItems() if type(i) is Pokeball]


def GetAllPotions():
  return [i for i in GetAllItems() if type(i) is Potion]


def GetAllCandies():
  return [i for i in GetAllItems() if type(i) is Candy]


def GetAllEvoItems():
  return [i for i in GetAllItems() if i.EvolutionItem]


def GetItem(id: int):
  return next(i for i in GetAllItems() if i.Id == id)


def GetPokeball(id: int):
  return next(i for i in GetAllPokeballs() if i.Id == id)


def GetPotion(id: int):
  return next(i for i in GetAllPotions() if i.Id == id)


def GetCandy(id: int):
  return next(i for i in GetAllCandies() if i.Id == id)


def TryGetCandy():
  if choice(range(1,101)) < 20:
    randCandy = choice(range(1,101))
    if randCandy < 10:
      return GetCandy(50) #Rare Candy
    elif randCandy < 40:
      return GetCandy(1185) #Large Candy
    return GetCandy(1183) #Small Candy
  return None


def GetEvoItem(id: int):
  return next(i for i in GetAllEvoItems() if i.Id == id)


def GetEgg(id: int):
  return next(e for e in eggda.GetAllEggs() if e.Id == id)