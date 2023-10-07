from typing import Dict


class Item:
  Id: int
  Name: str
  Description: str
  BuyAmount: int
  SellAmount: int

  def __init__(self, dict: Dict | None):
    self.Id = dict.get('Id') or 0 if dict else 0
    self.Name = dict.get('Name') or '' if dict else ''
    self.Description = dict.get('Description') or '' if dict else ''
    self.BuyAmount = dict.get('BuyAmount') or 0 if dict else 0
    self.SellAmount = dict.get('SellAmount') or 0 if dict else 0


class Pokeball(Item):
  CaptureRate: float

  def __init__(self, dict: Dict | None):
    self.CaptureRate = dict.get('CaptureRate') or 0.0 if dict else 0.0
    super(Pokeball, self).__init__(dict)


class Potion(Item):
  HealingAmount: int

  def __init__(self, dict: Dict | None):
    self.HealingAmount = dict.get('HealingAmount') or 0 if dict else 0
    super(Potion, self).__init__(dict)
