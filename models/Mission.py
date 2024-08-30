from dataclasses import dataclass, fields


class Mission:
	Id: int
	Amount: str
	Action: str
	Type: int|None
	Description: list[int]

	def __init__(self, dict):
		vars(self).update(dict)

@dataclass
class TrainerMission:
	Progress: int = 0
	DayStarted: str = ''
	MissionId: int = -1

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj