from dataaccess import gymda
from services import pokemonservice
from models.Pokemon import Pokemon, PokedexEntry
from models.Trainer import Trainer
from models.Gym import GymLeader

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()


def GetNextTrainerGym(trainer: Trainer):
	totalGyms = len(GetAllGymLeaders())
	for i in range(1, (totalGyms + 1)):
		if i not in trainer.Badges:
			return gymda.GetGymLeaderByBadgeId(i)
	return None


def GetGymLeaderTeam(leader: GymLeader):
	return [p for p in [pokemonservice.GetPokemonById(id) for id in leader.Team] if p]


def GymLeaderFight(trainerTeam: list[PokedexEntry], leaderTeam: list[Pokemon]):
	fightResults: list[int] = []

	while(trainerTeam and leaderTeam):
		trainerFighter = pokemonservice.GetPokemonById(trainerTeam[0].Pokemon.Pokemon_Id)
		if not trainerFighter:
			fightResults.append(-1)
			break
		else:
			fight = pokemonservice.PokemonFight(trainerFighter, leaderTeam[0], True)
			fightResults.append(fight)
			if fight == 1:
				leaderTeam.remove(leaderTeam[0])
			else:
				trainerTeam.remove(trainerTeam[0])
	return fightResults
