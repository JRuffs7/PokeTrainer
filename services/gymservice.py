from dataaccess import gymda
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from models.Gym import GymLeader

#region Gym Leaders

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()


def GetNextTrainerGym(trainerBadges: list[int]):
	badges = GetAllBadges()
	badges.sort(key=lambda b: b.Id)
	for b in badges:
		if b.Id not in trainerBadges:
			return gymda.GetGymLeaderByBadgeId(b.Id)
	return None


def GetBattleTeam(team: list[int]):
	return [p for p in [pokemonservice.GetPokemonById(id) for id in team] if p]


def GymLeaderFight(trainer: Trainer, leader: GymLeader):
	trainerTeam = [{ 'Pokemon': pokemonservice.GetPokemonById(t.Pokemon_Id), 'Id': t.Id } for t in trainerservice.GetTeam(trainer)]
	leaderTeam = GetBattleTeam(leader.Team)
	fightResults: list[int] = []
	expList: dict[str, int] = {}
	trainerInd = leaderInd = 0
	while trainerInd < len(trainerTeam) and leaderInd < len(leaderTeam):
		trainerFighter = trainerTeam[trainerInd]
		leaderFighter = leaderTeam[leaderInd]
		fight = pokemonservice.PokemonFight(trainerFighter['Pokemon'], leaderFighter, True)
		fightResults.append(fight)
		if fight == 1:
			expList[trainerTeam[trainerInd]['Id']] = 10*leaderTeam[leaderInd].Rarity
			leaderInd += 1
		else:
			trainerInd += 1

	for pId in expList:
		tPokemon = next(p for p in trainer.OwnedPokemon if pId == p.Id)
		tData = next(d['Pokemon'] for d in trainerTeam if d['Id'] == tPokemon.Id)
		pokemonservice.AddExperience(tPokemon, tData.Rarity, expList[pId])
	return fightResults


def GetGymLeaderByBadge(badgeId: int):
	return next(l for l in GetAllGymLeaders() if l.BadgeId == badgeId)

#endregion

#region Badges

def GetAllBadges():
	return gymda.GetAllBadges()

def GetBadgeById(badgeId: int):
	return next((b for b in GetAllBadges() if b.Id == badgeId),None)

def GetBadgesByRegion(generation: int):
	return [b for b in GetAllBadges() if b.Generation == generation]

#endregion