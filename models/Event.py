class Event:
	EventName: str
	EventType: int

	def __init__(self, dict):
		vars(self).update(dict)
