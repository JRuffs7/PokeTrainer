from dataaccess.utility.jsonreader import GetJson

from models.Gym import GymLeader, Badge, SpecialTrainer

leadersFile = "collections/gymleaders.json"
badgesFile = "collections/badges.json"
trainersFile = "collections/specialtrainers.json"

#region Gym Leaders

def GetAllGymLeaders():
  gyms = GetJson(leadersFile)
  return [GymLeader(g) for g in gyms]

#endregion

#region Badges

def GetAllBadges():
  badges = GetJson(badgesFile)
  return [Badge(b) for b in badges]

#endregion

#region Special Trainers

def GetAllSpecialTrainers():
  sTrainers = GetJson(trainersFile)
  return [SpecialTrainer(st) for st in sTrainers]

#endregion