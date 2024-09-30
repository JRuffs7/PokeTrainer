from dataclasses import dataclass, field, fields
from models.Base import Base


class Move:
  MoveId: int
  PP: int

  def __init__(self, dict):
    vars(self).update(dict)


class EvolveData:
  EvolveID: int
  EvolveLevel: int|None
  GenderNeeded: int|None
  ItemNeeded: int|None
  MoveNeeded: int|None

  def __init__(self, dict):
    vars(self).update(dict)


class PokemonData(Base):
  #Form Properties
  IsMega: bool
  IsBattleOnly: bool
  IsDefault: bool
  #Species Properties
  GrowthRate: str
  CaptureRate: int
  Color: str
  EvolvesInto: list[EvolveData]
  RandomEvolve: bool
  FemaleChance: int | None
  Generation: int
  PokedexId: int
  IsStarter: bool
  IsBaby: bool
  IsFossil: bool
  IsUltraBeast: bool
  IsParadox: bool
  IsLegendary: bool
  IsMythical: bool
  #Pokemon Properties
  BaseDefeatExp: int
  Height: int
  Sprite: str
  ShinySprite: str
  SpriteFemale: str
  ShinySpriteFemale: str
  Types: list[int]
  Weight: int
  Rarity: int
  LevelUpMoves: dict[str,int]
  MachineMoves: list[int]
  BaseStats: dict[str,int]

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
  Nature: int = 0
  CurrentHP: int = 0
  IVs: dict[str, int] = field(default_factory=dict)
  LearnedMoves: list[Move] = field(default_factory=list)
  CurrentAilment: int|None = None


  @classmethod
  def from_dict(cls, dict):
    field_names = {field.name for field in fields(cls)}
    returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
    returnObj.LearnedMoves = [Move(m) for m in returnObj.LearnedMoves]
    return returnObj