from typing import List

from flask import json

from models.Gym import GymLeader

leadersFile = "collections/gymleaders.json"

def GetAllGymLeaders():
  return [GymLeader(g) for g in GetJson(leadersFile)]


def GetGymLeaderByBadgeId(badgeId):
  return next((GymLeader(g) for g in GetJson() if g['BadgeId'] == badgeId), None)


def GetJson(file):
  with open(file, encoding="utf-8") as f:
    return json.load(f)