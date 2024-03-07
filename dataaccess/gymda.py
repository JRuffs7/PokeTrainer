from dataaccess.utility.jsonreader import GetJson

from models.Gym import GymLeader, Badge

leadersFile = "collections/gymleaders.json"
badgesFile = "collections/badges.json"

#region Gym Leaders

def GetAllGymLeaders():
  return [GymLeader(g) for g in GetJson(leadersFile)]

#endregion

#region Badges

def GetAllBadges():
  return [Badge(b) for b in GetJson(badgesFile)]

#endregion