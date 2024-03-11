class Event:
	EventName: str
	EventType: int
	MessageId: int
	SubType: int|None
	EventEntries: dict[int, any]

	def __init__(self, dict):
		vars(self).update(dict)
