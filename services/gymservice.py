from dataaccess import gymda
from services import pokemonservice, trainerservice
from models.Trainer import Trainer
from models.Pokemon import Pokemon
from models.Gym import GymLeader

#region Gym Leaders

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()


def GetNextTrainerGym(trainer: Trainer):
	badges = GetAllBadges()
	badges.sort(key=lambda b: b.Id)
	for b in badges:
		if b.Id not in trainer.Badges:
			return next((g for g in GetAllGymLeaders() if g.BadgeId == b.Id),None)
	return None


def GetGymLeaderTeam(leader: GymLeader):
	return [p for p in [pokemonservice.GetPokemonById(id) for id in leader.Team] if p]


def GymLeaderFight(trainer: Trainer, leaderTeam: list[Pokemon], reward: int, badgeId: int):
	trainerTeam = [t for t in trainerservice.GetTeam(trainer) if t]
	fightResults: list[int] = []
	expList: dict[str, int] = {}
	trainerInd = leaderInd = 0
	while (trainerInd < len(trainerTeam)) and (leaderInd < len(leaderTeam)):
		trainerFighter = pokemonservice.GetPokemonById(trainerTeam[trainerInd].Pokemon.Pokemon_Id)
		if not trainerFighter:
			fightResults.append(-1)
			break
		else:
			fight = pokemonservice.PokemonFight(trainerFighter, leaderTeam[leaderInd], True)
			fightResults.append(fight)
			if fight == 1:
				expList[trainerTeam[trainerInd].Id] = 10*leaderTeam[leaderInd].Rarity
				leaderInd += 1
			else:
				trainerInd += 1

	if -1 not in fightResults:
		for i in expList:
			next(t for t in trainerTeam if t.Id == i).GainExp(expList[i])
		if leaderInd >= len(leaderTeam):
			trainer.Money += reward
			trainer.Badges.append(badgeId)
		trainerservice.UpsertTrainer(trainer)
	return fightResults

#endregion

#region Badges

def GetAllBadges():
	return gymda.GetAllBadges()

def GetBadgeById(badgeId: int):
	return next((b for b in GetAllBadges() if b.Id == badgeId),None)

def GetBadgesByRegion(generation: int):
	return [b for b in GetAllBadges() if b.Generation == generation]

#endregion