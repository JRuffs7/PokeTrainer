from dataaccess.utility.jsonreader import GetJson

from models.Cpu import CpuTrainer, Badge

badgesFile = "collections/badges.json"
trainersFile = "collections/cputrainers.json"

#region Gym Leaders

def GetAllGymLeaders():
  gyms = GetJson(trainersFile)
  return [CpuTrainer.from_dict(g) for g in gyms['GymLeaders']]

#endregion

#region Elite Four

def GetAllEliteFour():
  gyms = GetJson(trainersFile)
  return [CpuTrainer.from_dict(g) for g in gyms['EliteFour']]

#endregion

#region NPC Trainers

def GetAllNPCTrainers():
  gyms = GetJson(trainersFile)
  return [CpuTrainer.from_dict(g) for g in gyms['NPCTrainers']]

#endregion

#region Badges

def GetAllBadges():
  badges = GetJson(badgesFile)
  return [Badge(b) for b in badges]

#endregion