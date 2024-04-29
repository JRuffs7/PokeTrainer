from dataclasses import dataclass, fields


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
  RandomEvolve: bool
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


@dataclass
class Pokemon:
  Id: str = ''
  Pokemon_Id: int = 0
  Nickname: str|None = None
  Height: float = 0
  Weight: float = 0
  IsShiny: bool = False
  IsFemale: bool|None = None
  Level: int = 0
  CurrentExp: int = 0

  @classmethod
  def from_dict(cls, dict):
    field_names = {field.name for field in fields(cls)}
    returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
    return returnObj

  # def __init__(self, dict):
  #   vars(self).update(dict)