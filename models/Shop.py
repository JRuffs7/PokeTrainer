class SpecialShop:
	LastRecycle: str|None
	ItemIds: list[int]

	def __init__(self, dict):
		vars(self).update(dict)