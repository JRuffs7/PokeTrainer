from dataaccess import eggda, itemda


def GetFullShop():
  pokeballs = [p for p in itemda.GetAllPokeballs()]
  potions = [p for p in itemda.GetAllPotions()]
  return (pokeballs, potions)


def GetPokeball(id: int):
  return next(p for p in itemda.GetAllPokeballs() if p.Id == id)


def GetPotion(id: int):
  return next(p for p in itemda.GetAllPotions() if p.Id == id)


def GetEgg(id: int):
  return next(e for e in eggda.GetAllEggs() if e.Id == id)