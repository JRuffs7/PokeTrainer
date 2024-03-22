class Zone:
	Id: int
	Name: str
	Types: list[str]
	FightOnly: bool

	def __init__(self, dict):
		vars(self).update(dict)