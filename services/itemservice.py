from dataaccess import eggda, itemda


def GetAllPokeballs():
  return itemda.GetAllPokeballs()


def GetAllPotions():
  return itemda.GetAllPotions()


def GetAllCandies():
  return itemda.GetAllCandies()


def GetPokeball(id: int):
  return next(p for p in itemda.GetAllPokeballs() if p.Id == id)


def GetPotion(id: int):
  return next(p for p in itemda.GetAllPotions() if p.Id == id)


def GetCandy(id: int):
  return next(c for c in itemda.GetAllCandies() if c.Id == id)


def GetEgg(id: int):
  return next(e for e in eggda.GetAllEggs() if e.Id == id)