from dataaccess import itemda


def GetFullShop():
  pokeballs = [p for p in itemda.GetAllPokeballs() if p.BuyAmount > 0]
  potions = itemda.GetAllPotions()
  return (pokeballs, potions)


def GetPokeball(id):
  return itemda.GetPokeballById(id)


def GetPotion(id):
  return itemda.GetPotionById(id)
