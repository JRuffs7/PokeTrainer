from dataclasses import dataclass, fields

class Egg:
	Id: int
	Name: str
	Hatch: list[int]
	SpawnsNeeded: int
	Sprite: str

	def __init__(self, dict):
		vars(self).update(dict)
	
@dataclass
class TrainerEgg:
	Id: str = ''
	EggId: int = 0
	SpawnCount: int = 0

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj