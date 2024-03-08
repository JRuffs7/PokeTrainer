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
			return next(g for g in gymda.GetAllGymLeaders() if g.BadgeId == b.Id)
	return None


def GetBattleTeam(team: list[int]):
	return [p for p in [pokemonservice.GetPokemonById(id) for id in team] if p]


def GymLeaderFight(trainer: Trainer, leader: GymLeader):
	trainerTeam = [{ 'Pokemon': pokemonservice.GetPokemonById(t.Pokemon_Id), 'Id': t.Id } for t in trainerservice.GetTeam(trainer)]
	leaderTeam = GetBattleTeam(leader.Team)
	fightResults: list[bool] = []
	expList: dict[str, int] = {}
	trainerInd = leaderInd = 0
	while trainerInd < len(trainerTeam) and leaderInd < len(leaderTeam):
		trainerFighter = trainerTeam[trainerInd]
		leaderFighter = leaderTeam[leaderInd]
		fight = pokemonservice.GymFight(trainerFighter['Pokemon'], leaderFighter)
		fightResults.append(fight)
		if fight:
			expList[trainerTeam[trainerInd]['Id']] = 10*leaderTeam[leaderInd].Rarity
			leaderInd += 1
		else:
			trainerInd += 1

	for pId in expList:
		tPokemon = next(p for p in trainer.OwnedPokemon if pId == p.Id)
		tData = next(d['Pokemon'] for d in trainerTeam if d['Id'] == tPokemon.Id)
		pokemonservice.AddExperience(tPokemon, tData, expList[pId])
	return fightResults


def GetGymLeaderByBadge(badgeId: int):
	return next(l for l in GetAllGymLeaders() if l.BadgeId == badgeId)

#endregion

#region Badges

def GetAllBadges():
	return gymda.GetAllBadges()

def GetBadgeById(badgeId: int):
	return next((b for b in GetAllBadges() if b.Id == badgeId),None)

def GetGymBadges(trainer: Trainer, generation: int):
  badgeList = [ba for ba in [GetBadgeById(b) for b in trainer.Badges] if ba]
  if generation:
    badgeList = [b for b in badgeList if b.Generation == generation]
  badgeList.sort(key=lambda x: x.Id)
  return badgeList

def GymCompletion(trainer: Trainer, generation: int = None):
  allBadges = [b.Id for b in GetAllBadges() if (b.Generation == generation if generation else True)]
  obtained = list(filter(allBadges.__contains__, trainer.Badges))
  return (len(obtained), len(allBadges))

#endregion