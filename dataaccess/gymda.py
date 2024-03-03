from typing import List

from flask import json

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

def GetJson(file):
  with open(file, encoding="utf-8") as f:
    return json.load(f)