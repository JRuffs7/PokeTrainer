from models.Base import Base

class Item(Base):
  Sprite: str|None
  Description: str
  EvolutionItem: bool
  BuyAmount: int
  SellAmount: int

  def __init__(self, dict):
    super(Item, self).__init__(dict)


class Pokeball(Item):
  CaptureRate: float

  def __init__(self, dict):
    super(Pokeball, self).__init__(dict)


class Potion(Item):
  HealingAmount: int|None
  AilmentCures: list[int]

  def __init__(self, dict):
    super(Potion, self).__init__(dict)


class Candy(Item):
  Experience: int|None

  def __init__(self, dict):
    super(Candy, self).__init__(dict)