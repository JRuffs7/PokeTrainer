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
  Id: str
  Pokemon_Id: int
  Height: float
  Weight: float
  IsShiny: bool
  IsFemale: bool
  Level: int
  CurrentExp: int

  def __init__(self, dict):
    vars(self).update(dict)
    # self.Id = dict.get('Id') or uuid.uuid4().hex if dict else uuid.uuid4().hex
    # self.Pokemon_Id = dict.get('Pokemon_Id') or 0 if dict else 0
    # self.Height = dict.get('Height') or 0.0 if dict else 0.0
    # self.Weight = dict.get('Weight') or 0.0 if dict else 0.0
    # self.IsShiny = dict.get('IsShiny') or False if dict else False
    # self.IsFemale = dict.get('IsFemale') or False if dict else False
    # self.Level = dict.get('Pokemon_Id') or 0 if dict else 0
    # self.CurrentExp = dict.get('Pokemon_Id') or 0 if dict else 0
