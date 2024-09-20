from dataaccess.utility.jsonreader import GetJson

from models.Cpu import CpuTrainer, Badge

leadersFile = "collections/gymleaders.json"
badgesFile = "collections/badges.json"
trainersFile = "collections/specialtrainers.json"

#region Gym Leaders

def GetAllGymLeaders():
  gyms = GetJson(leadersFile)
  return [CpuTrainer.from_dict(g) for g in gyms if g['BadgeId']]

#endregion

#region Badges

def GetAllBadges():
  badges = GetJson(badgesFile)
  return [Badge(b) for b in badges]

#endregion

#region Special Trainers

def GetAllSpecialTrainers():
  sTrainers = GetJson(trainersFile)
  return [CpuTrainer.from_dict(st) for st in sTrainers]

#endregion