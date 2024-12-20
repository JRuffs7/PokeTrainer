from random import choice
from dataaccess import missionda
from models.Mission import Mission


def GetAllDailyMissions():
	return missionda.GetAllMissions('Daily')

def GetDailyMission(missionId: int):
	return next(m for m in GetAllDailyMissions() if m.Id == missionId)

def GetNewDailyMission():
	return choice(GetAllDailyMissions())

def GetAllWeeklyMissions():
	return missionda.GetAllMissions('Weekly')

def GetWeeklyMission(missionId: int):
	return next(m for m in GetAllWeeklyMissions() if m.Id == missionId)

def GetNewWeeklyMission():
	return choice(GetAllWeeklyMissions())

def CheckMissionType(mission: Mission, types: list[int]):
	return (not mission.Type) or (mission.Type in types)