from dataaccess import gymda
from services import pokemonservice
from models.Pokemon import Pokemon, PokedexEntry
from models.Gym import GymLeader

#region Gym Leaders

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()


def GetNextTrainerGym(trainerBadges: list[int]):
	badges = GetAllBadges()
	badges.sort(key=lambda b: b.Id)
	for b in badges:
		if b.Id not in trainerBadges:
			return next((g for g in GetAllGymLeaders() if g.BadgeId == b.Id),None)
	return None


def GetGymLeaderTeam(leader: GymLeader):
	return [p for p in [pokemonservice.GetPokemonById(id) for id in leader.Team] if p]


def GymLeaderFight(trainerTeam: list[PokedexEntry], leaderTeam: list[Pokemon]):
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