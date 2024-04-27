from dataaccess import eggda, itemda


def GetAllItems():
  return itemda.GetAllItems()


def GetAllPokeballs():
  return itemda.GetAllPokeballs()


def GetAllPotions():
  return itemda.GetAllPotions()


def GetAllCandies():
  return itemda.GetAllCandies()


def GetItem(id: int):
  return next(i for i in itemda.GetAllItems() if i.Id == id)


def GetPokeball(id: int):
  return next(p for p in itemda.GetAllPokeballs() if p.Id == id)


def GetPotion(id: int):
  return next(p for p in itemda.GetAllPotions() if p.Id == id)


def GetCandy(id: int):
  return next(c for c in itemda.GetAllCandies() if c.Id == id)


def GetEgg(id: int):
  return next(e for e in eggda.GetAllEggs() if e.Id == id)