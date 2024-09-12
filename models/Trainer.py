from dataclasses import dataclass, field, fields
from models.Egg import TrainerEgg
from models.Mission import TrainerMission
from models.Pokemon import Pokemon
from models.Shop import SpecialShop

@dataclass
class Trainer:
  UserId: int = 0
  ServerId: int = 0
  Health: int = 0
  Money: int = 0
  Items: dict[str, int] = field(default_factory=dict)
  OwnedPokemon: list[Pokemon] = field(default_factory=list)
  Pokedex: list[int] = field(default_factory=list)
  Shinydex: list[int] = field(default_factory=list)
  Formdex: list[int] = field(default_factory=list)
  Team: list[str] = field(default_factory=list)
  Badges: list[int] = field(default_factory=list)
  SpTrainerWins: list[int] = field(default_factory=list)
  GymAttempts: list[int] = field(default_factory=list)
  Eggs: list[TrainerEgg] = field(default_factory=list)
  Daycare: dict[str, str] = field(default_factory=dict)
  Wishlist: list[int] = field(default_factory=list)
  LastDaily: str | None = None
  Shop: SpecialShop | None = field(default_factory=lambda: None)
  CurrentZone: int = 0
  DailyMission: TrainerMission | None = None
  WeeklyMission: TrainerMission | None = None

  @classmethod
  def from_dict(cls, dict):
    field_names = {field.name for field in fields(cls)}
    returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
    returnObj.OwnedPokemon = [Pokemon.from_dict(p) for p in returnObj.OwnedPokemon]
    returnObj.Eggs = [TrainerEgg.from_dict(e) for e in returnObj.Eggs]
    returnObj.Shop = SpecialShop(returnObj.Shop) if returnObj.Shop else None
    returnObj.DailyMission = TrainerMission.from_dict(returnObj.DailyMission) if returnObj.DailyMission else None
    returnObj.WeeklyMission = TrainerMission.from_dict(returnObj.WeeklyMission) if returnObj.WeeklyMission else None
    return returnObj
