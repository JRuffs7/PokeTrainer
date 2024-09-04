from models.Pokemon import Pokemon


class GymLeader:
	Name: str
	Generation: int
	MainType: str
	Sprite: str
	Team: list[int]
	BadgeId: int
	Reward: int

	def __init__(self, dict):
		vars(self).update(dict)


class Badge:
	Id: int
	Name: str
	Generation: int
	Sprite: str

	def __init__(self, dict):
		vars(self).update(dict)


class SpecialTrainer:
	Id: int
	Name: str
	Sprite: str
	Team: list[Pokemon]
	Reward: tuple[int,int]

	def __init__(self, dict):
		vars(self).update(dict)

class GymLeader(SpecialTrainer):
	Generation: int
	MainType: str
	BadgeId: int

	def __init__(self, dict):
		vars(self).update(dict)