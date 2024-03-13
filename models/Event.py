class Event:
	EventName: str
	EventType: int
	MessageId: int
	ThreadId: int|None
	SubType: int|None
	EventEntries: dict[str, str]

	def __init__(self, dict):
		vars(self).update(dict)
