import uuid
from typing import Dict, List


class Pokemon:
  #Form Properties
  Id: int
  IsMega: bool
  IsBattleOnly: bool
  IsDefault: bool
  #Species Properties
  CaptureRate: int
  Color: str
  EvolvesInto: List[int]
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
  Types: List[str]
  Weight: int
  Rarity: int

  def __init__(self, dict: Dict | None):
    self.Id = dict.get('Id') or 0 if dict else 0
    self.IsMega = dict.get('IsMega') or False if dict else False
    self.IsBattleOnly = dict.get('IsBattleOnly') or False if dict else False
    self.IsDefault = dict.get('IsDefault') or False if dict else False

    self.CaptureRate = dict.get('CaptureRate') or 0 if dict else 0
    self.Color = dict.get('Color') or '' if dict else ''
    evo = dict.get('EvolvesInto') if dict else []
    self.EvolvesInto = evo or [] if isinstance(
        evo, List) else evo.value if evo else []
    self.FemaleChance = dict.get('FemaleChance') or None if dict else None
    self.Generation = dict.get('Generation') or 0 if dict else 0
    self.Name = dict.get('Name') or '' if dict else ''
    self.PokedexId = dict.get('PokedexId') or 0 if dict else 0
    self.IsBaby = dict.get('IsBaby') or False if dict else False
    self.IsLegendary = dict.get('IsLegendary') or False if dict else False
    self.IsMythical = dict.get('IsMythical') or False if dict else False

    self.Height = dict.get('Height') or 0 if dict else 0
    self.Sprite = dict.get('Sprite') or '' if dict else ''
    self.ShinySprite = dict.get('ShinySprite') or '' if dict else ''
    self.SpriteFemale = dict.get('SpriteFemale') or '' if dict else ''
    self.ShinySpriteFemale = dict.get(
        'ShinySpriteFemale') or '' if dict else ''
    types = dict.get('Types') if dict else []
    self.Types = types or [] if isinstance(
        types, List) else types.value if types else []
    self.Weight = dict.get('Weight') or 0 if dict else 0
    self.Rarity = dict.get('Rarity') or 0 if dict else 0

  def GetImage(self, isShiny, isFemale):
    if isShiny and isFemale:
      return self.ShinySpriteFemale or self.ShinySprite
    elif isShiny and not isFemale:
      return self.ShinySprite
    elif not isShiny and isFemale:
      return self.SpriteFemale or self.Sprite
    return self.Sprite


class SpawnPokemon:
  Id: str
  Pokemon_Id: int
  Height: float
  Weight: float
  IsShiny: bool
  IsFemale: bool

  def __init__(self, dict: Dict | None):
    self.Id = dict.get('Id') or uuid.uuid4().hex if dict else uuid.uuid4().hex
    self.Pokemon_Id = dict.get('Pokemon_Id') or 0 if dict else 0
    self.Height = dict.get('Height') or 0.0 if dict else 0.0
    self.Weight = dict.get('Weight') or 0.0 if dict else 0.0
    self.IsShiny = dict.get('IsShiny') or False if dict else False
    self.IsFemale = dict.get('IsFemale') or False if dict else False
