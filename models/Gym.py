from typing import List, Dict

class GymLeader:
	Name: str
	Generation: int
	Sprite: str
	Team: List[int]
	BadgeId: int
	Reward: int

	def __init__(self, dict: Dict):
		self.Name = dict.get("Name") or ''
		self.Generation = dict.get("Generation") or 0
		self.Sprite = dict.get("Sprite") or ''
		self.Team = dict.get("Team") or []
		self.BadgeId = dict.get("BadgeId") or 0
		self.Reward = dict.get("Reward") or 0


class Badge:
	Id: int
	Name: str
	Generation: int
	Sprite: str

	def __init__(self, dict: Dict):
		self.Id = dict.get("Id") or 0
		self.Name = dict.get("Name") or ''
		self.Generation = dict.get("Generation") or 0
		self.Sprite = dict.get("Sprite") or ''