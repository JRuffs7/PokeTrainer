from dataclasses import dataclass, fields
from models.Base import Base

class Egg(Base):
	Hatch: list[int]
	SpawnsNeeded: int
	Sprite: str

	def __init__(self, dict):
		super(Egg, self).__init__(dict)
	
@dataclass
class TrainerEgg:
	Id: str = ''
	EggId: int = 0
	Generation: int = 1
	SpawnCount: int = 0

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj