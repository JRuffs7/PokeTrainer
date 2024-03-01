from models.enums import EventType


class Event:
	EventId: str
	EventName: str
	EventType: EventType
	UserInteractions: list[int]

	def __init__(self, dict):
		vars(self).update(dict)



