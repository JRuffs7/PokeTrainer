from typing import List, Dict

class GymLeader:
	Name: str
	Team: List[int]
	BadgeId: int
	Reward: int

	def __init__(self, dict: Dict):
		self.Name = dict.get("Name") or ''
		self.Team = dict.get("Team") or []
		self.BadgeId = dict.get("BadgeId") or 0
		self.Reward = dict.get("Reward") or 0