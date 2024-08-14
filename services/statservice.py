import math

from dataaccess import statda

#region Nature

def GetAllNatures():
	return statda.GetAllNatures()

def GetNature(id: int):
	return next(n for n in GetAllNatures() if n.Id == id)

#region Types

def GetAllTypes():
	return statda.GetAllTypes()

def GetType(id: int):
	return next(t for t in GetAllTypes() if t.Id == id)

#region Stats

def GenerateHP(iv: int, base: int, level: int, ev: int = 0):
	return math.floor((((2 * base) + iv + math.floor(ev/4)) * level)/100) + level + 10

def GenerateSubStat(iv: int, base: int, level: int, nature: float, ev: int = 0):
	return math.floor((math.floor((((2 * base) + iv + math.floor(ev/4)) * level)/100) + 5) * nature)
