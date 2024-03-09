class PokemonData:
  #Form Properties
  Id: int
  IsMega: bool
  IsBattleOnly: bool
  IsDefault: bool
  #Species Properties
  CaptureRate: int
  Color: str
  EvolvesInto: list[int]
  FemaleChance: int | None
  Generation: int
  Name: str
  PokedexId: int
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


class Pokemon:
  Id: str = ''
  Pokemon_Id: int = 0
  Height: float = 0
  Weight: float = 0
  IsShiny: bool = False
  IsFemale: bool = False
  Level: int = 0
  CurrentExp: int = 0

  def __init__(self, dict):
    vars(self).update(dict)