import math

from dataaccess import statda
from models.Pokemon import Pokemon, PokemonData
from models.Stat import StatEnum

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

def TypeDamage(moveType: int, defendingTypes: int):
	defendTypes = [t for t in GetAllTypes() if t.Id in defendingTypes]
	damage = 1
	for t in defendTypes:
		if moveType in t.Immune:
			return 0
		if moveType in t.Weakness:
			damage *= 2
		if moveType in t.Resistant:
			damage = damage/2
	return damage


#region Stats

def GenerateStat(pokemon: Pokemon, data: PokemonData, stat: StatEnum):
	if stat == StatEnum.HP:
		iv = GetIV(pokemon, 'hp')
		base = GetBaseStat(data, 'hp')
		ev = 0
		return math.floor((((2 * base) + iv + math.floor(ev/4)) * pokemon.Level)/100) + pokemon.Level + 10
	else:
		iv = GetIV(pokemon, stat.name.replace(' ', '').lower())
		base = GetBaseStat(data, stat.name.replace(' ', '').lower())
		ev = 0
		return math.floor((math.floor((((2 * base) + iv + math.floor(ev/4)) * pokemon.Level)/100) + 5) * CheckNatureBoost(pokemon, stat.name.replace(' ', '').lower()))

def GetIV(pokemon: Pokemon, st: str):
	stat = next(s for s in statda.GetAllStats() if s.Name.replace(' ', '').lower() == st)
	return pokemon.IVs[str(stat.Id)]

def GetBaseStat(pokemon: PokemonData, st: str):
	stat = next(s for s in statda.GetAllStats() if s.Name.replace(' ', '').lower() == st)
	return pokemon.BaseStats[str(stat.Id)]

def CheckNatureBoost(pokemon: Pokemon, st: str):
	stat = next(s for s in statda.GetAllStats() if s.Name.replace(' ', '').lower() == st)
	nature = next(n for n in statda.GetAllNatures() if n.Id == pokemon.Nature)
	if stat.Id in nature.StatBoost:
		return 1.1
	elif stat.Id in nature.StatDecrease:
		return 0.9
	return 1

def ExpCalculator(pokemon: Pokemon, data: PokemonData):
	currLevel = pokemon.Level
	nextLevel = pokemon.Level + 1

	if currLevel == 100:
		return 0

	if data.GrowthRate.lower() == 'medium':
		expToCurrentLvl = math.floor(math.pow(currLevel,3))
		expToNextLvl = math.floor(math.pow(nextLevel,3))

	elif data.GrowthRate.lower() == 'fast':
		expToCurrentLvl = math.floor((4*math.pow(currLevel,3))/5)
		expToNextLvl = math.floor((4*math.pow(nextLevel,3))/5)

	elif data.GrowthRate.lower() == 'mediumslow':
		expToCurrentLvl = math.floor(((6*math.pow(currLevel,3))/5) - (15*math.pow(currLevel,2)) + (100*currLevel) - 140)
		expToNextLvl = math.floor(((6*math.pow(nextLevel,3))/5) - (15*math.pow(nextLevel,2)) + (100*nextLevel) - 140)

	elif data.GrowthRate.lower() == 'erratic':
		if currLevel < 50:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(100 - currLevel))/50)
		elif currLevel < 68:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(150 - currLevel))/100)
		elif currLevel < 98:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(math.floor(1911 - (10*currLevel)/3)))/500)
		else:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(160 - currLevel))/100)

		if nextLevel < 50:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(100 - nextLevel))/50)
		elif nextLevel < 68:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(150 - nextLevel))/100)
		elif nextLevel < 98:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(math.floor(1911 - (10*nextLevel)/3)))/500)
		else:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(160 - nextLevel))/100)

	elif data.GrowthRate.lower() == 'fluctuating':
		if currLevel < 15:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(math.floor((currLevel + 1)/3) + 24))/50)
		elif currLevel < 36:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(currLevel + 14))/50)
		else:
			expToCurrentLvl = math.floor((math.pow(currLevel,3)*(math.floor(currLevel/2) + 32))/50)

		if nextLevel < 15:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(math.floor((nextLevel + 1)/3) + 24))/50)
		elif nextLevel < 36:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(nextLevel + 14))/50)
		else:
			expToNextLvl = math.floor((math.pow(nextLevel,3)*(math.floor(nextLevel/2) + 32))/50)
	
	else: #slow
		expToCurrentLvl = math.floor((5*math.pow(currLevel,3))/4)
		expToNextLvl = math.floor((5*math.pow(nextLevel,3))/4)


	return (expToCurrentLvl, expToNextLvl)