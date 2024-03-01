from dataaccess import itemda


def GetFullShop():
  pokeballs = [p for p in itemda.GetAllPokeballs() if p.BuyAmount]
  potions = [p for p in itemda.GetAllPotions() if p.BuyAmount]
  return (pokeballs, potions)


def GetPokeball(id: int):
  return itemda.GetPokeballById(id)


def GetPotion(id: int):
  return itemda.GetPotionById(id)
