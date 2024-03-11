class Event:
	EventId: str
	EventName: str
	EventType: int

	def __init__(self, dict):
		vars(self).update(dict)
