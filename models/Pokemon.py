class EvolveData:
  EvolveID: int
  EvolveLevel: int|None
  GenderNeeded: int|None
  ItemNeeded: int|None

  def __init__(self, dict):
    vars(self).update(dict)


class PokemonData:
  #Form Properties
  Id: int
  IsMega: bool
  IsBattleOnly: bool
  IsDefault: bool
  #Species Properties
  CaptureRate: int
  Color: str
  EvolvesInto: list[EvolveData]
  FemaleChance: int | None
  Generation: int
  Name: str
  PokedexId: int
  IsStarter: bool
  IsBaby: bool
  IsFossil: bool
  IsUltraBeast: bool
  IsParadox: bool
  IsLegendary: bool
  IsMythical: bool
  #Pokemon Properties
  Height: int
  Sprite: str
  ShinySprite: str
  SpriteFemale: str
  ShinySpriteFemale: str
  Types: list[str]
  Weight: int
  Rarity: int

  def __init__(self, dict):
    vars(self).update(dict)
    self.EvolvesInto = [EvolveData(e) for e in self.EvolvesInto]


class Pokemon:
  Id: str
  Pokemon_Id: int
  Height: float
  Weight: float
  IsShiny: bool
  IsFemale: bool|None
  Level: int
  CurrentExp: int

  def __init__(self, dict):
    vars(self).update(dict)