from dataaccess.utility.jsonreader import GetJson

from models.Mission import Mission

missionFile = "collections/missions.json"

def GetAllMissions(missionType: str):
  missions = GetJson(missionFile)
  return [Mission(m) for m in missions[missionType]]