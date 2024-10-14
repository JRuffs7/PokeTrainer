from dataclasses import dataclass, field, fields
from models.Base import Base
from globals import ShinyOdds

@dataclass
class TrainerEgg:
	Id: str = ''
	Sprite: str = 'https://imgur.com/NabZl4k.png'
	Generation: int = 0
	OffspringId: int = 0
	SpawnCount: int = 0
	SpawnsNeeded: int = 0
	ShinyOdds: int = ShinyOdds
	IVs: dict[str,int] = field(default_factory=dict)

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj