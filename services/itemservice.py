from random import choice
from dataaccess import eggda, itemda
from models.Item import Candy, Pokeball, Potion
from models.Trainer import Trainer


def GetAllItems():
  return itemda.GetAllItems()


def GetAllPokeballs():
  return itemda.GetAllPokeballs()


def GetAllPotions():
  return itemda.GetAllPotions()


def GetAllCandies():
  return itemda.GetAllCandies()


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
  if choice(range(100)) < 20:
    randCandy = choice(range(100))
    if randCandy < 3:
      return GetCandy(50) #Rare Candy
    elif randCandy < 8:
      return GetCandy(1186) #XLarge Candy
    elif randCandy < 18:
      return GetCandy(1186) #Large Candy
    elif randCandy < 33:
      return GetCandy(1186) #Medium Candy
    elif randCandy < 58:
      return GetCandy(1186) #Small Candy
    return GetCandy(1183) #XSmall Candy
  return None


def GetEvoItem(id: int):
  return next(i for i in GetAllEvoItems() if i.Id == id)


def GetEgg(id: int):
  return next(e for e in eggda.GetAllEggs() if e.Id == id)

def GetTrainerPokeballs(trainer: Trainer):
  return [p for p in GetAllPokeballs() if str(p.Id) in trainer.Items and trainer.Items[str(p.Id)] > 0]

def GetTrainerPotions(trainer: Trainer):
  return [p for p in GetAllPotions() if str(p.Id) in trainer.Items and trainer.Items[str(p.Id)] > 0]