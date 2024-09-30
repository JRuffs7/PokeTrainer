from random import uniform
from dataaccess import gymda
from models.Pokemon import Pokemon
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import pokemonservice, statservice

#region Gym Leaders

def GetAllGymLeaders():
	return gymda.GetAllGymLeaders()

def GetGymLeaderByBadge(badgeId: int):
	return next((l for l in GetAllGymLeaders() if l.BadgeId == badgeId),None)

def SetUpGymBattle(leaderTeam: list[Pokemon]):
	dataList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in leaderTeam])
	for p in leaderTeam:
		data = next(po for po in dataList if po.Id == p.Pokemon_Id)
		p.Height = round(uniform((data.Height * 0.9), (data.Height * 1.1)) / 10, 2)
		p.Weight = round(uniform((data.Weight * 0.9), (data.Weight * 1.1)) / 10, 2)
		p.CurrentAilment = None
		p.CurrentExp = 0
		p.CurrentHP = statservice.GenerateStat(p, data, StatEnum.HP)

#endregion

#region Elite Four

def GetAllEliteFour():
	return gymda.GetAllGymLeaders()

def GetEliteFourByRegion(region: int):
	return [l for l in GetAllEliteFour() if l.Generation == region]

#endregion

#region Badges

def GetAllBadges():
	return gymda.GetAllBadges()

def GetBadgesByRegion(region: int):
	return [b for b in gymda.GetAllBadges() if b.Generation == region]

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
