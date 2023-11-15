from dataaccess import gymda
from models.Trainer import Trainer

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()


def GetNextTrainerGym(trainer: Trainer):
	totalGyms = len(GetAllGymLeaders())
	for i in range(1, (totalGyms + 1)):
		if i not in trainer.Badges:
			return gymda.GetGymLeaderByBadgeId(i)
	return None