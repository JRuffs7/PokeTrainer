from dataclasses import dataclass, field, fields
from models.Pokemon import Pokemon

class Badge:
	Id: int
	Name: str
	Generation: int
	Sprite: str

	def __init__(self, dict):
		vars(self).update(dict)

@dataclass
class CpuTrainer:
	Id: int = 0
	Name: str = ''
	Sprite: str = ''
	Team: list[Pokemon] = field(default_factory=list)
	Reward: tuple[int,int] = field(default_factory=tuple)
	Generation: int = 0
	MainType: str = ''
	BadgeId: int|None = None

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		returnObj.Team = [Pokemon.from_dict(p) for p in returnObj.Team]
		returnObj.Reward = (returnObj.Reward['Item1'], returnObj.Reward['Item2'])
		return returnObj