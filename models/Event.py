from dataclasses import dataclass, field, fields


@dataclass
class Event:
	EventName: str = ''
	EventType: int = 0
	MessageId: int = 0
	ThreadId: int|None = None
	SubType: int|None = None
	EventEntries: dict[str, str] = field(default_factory=dict)

	def __init__(self, dict):
		vars(self).update(dict)

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj