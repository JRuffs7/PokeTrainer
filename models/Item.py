
class Item:
  Id: int
  Name: str
  Description: str
  BuyAmount: int
  SellAmount: int

  def __init__(self, dict):
    vars(self).update(dict)


class Pokeball(Item):
  CaptureRate: float

  def __init__(self, dict):
    super(Pokeball, self).__init__(dict)


class Potion(Item):
  HealingAmount: int

  def __init__(self, dict):
    super(Potion, self).__init__(dict)
