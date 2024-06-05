from random import choice
from models.Pokemon import PokemonData
from services import pokemonservice, typeservice


def WildFight(attack: PokemonData, defend: PokemonData, attackLevel: int, defendLevel: int):
  healthLost: list[int] = [1,3,5,7,10,13,15]
  battleResult = typeservice.TypeMatch(attack.Types, defend.Types)
  doubleAdv = battleResult >= 2
  doubleDis = battleResult <= -2
  immune = battleResult == -5
  attackGroup = pokemonservice.RarityGroup(attack) % 7
  defendGroup = pokemonservice.RarityGroup(defend)
  levelAdvantage = 2 if attackLevel > (defendLevel*2) else 1 if attackLevel > (defendLevel*1.5) else 0
  levelDisadvantage = 2 if defendLevel > (attackLevel*2) else 1 if defendLevel > (attackLevel*1.5) else 0
  if attackLevel < 10 and defendLevel < 10:
    levelAdvantage = 1 if attackLevel > (defendLevel + 3) else 0 
    levelDisadvantage = 1 if defendLevel > (attackLevel + 3) else 0 
  
  if attackGroup - defendGroup == 0:
    returnInd = 6 if immune else 2 if doubleAdv else 4 if doubleDis else 3
  # 3v2 2v1
  elif attackGroup - defendGroup == 1:
    returnInd = 5 if immune else 1 if doubleAdv else 3 if doubleDis else 2
  # 3v1
  elif attackGroup - defendGroup == 2:
    returnInd = 4 if immune else 0 if doubleAdv else 2 if doubleDis else 1
  # 1v2 2v3
  elif attackGroup - defendGroup == -1:
    returnInd = 6 if immune else 3 if doubleAdv else 5 if doubleDis else 4
  # 1v3
  else:
    returnInd = 6 if immune else 4 if doubleAdv else 6 if doubleDis else 5
  returnInd -= (levelAdvantage - levelDisadvantage) if not immune else 0
  returnInd = 0 if returnInd < 0 else len(healthLost)-1 if returnInd >= len(healthLost) else returnInd
  lost = healthLost[returnInd] - battleResult
  lost = lost - (1 if attack.Rarity == 10 else 0)
  return lost if lost > 0 else 1

def GymFight(attack: PokemonData, defend: PokemonData, attackLevel: int, gymID: int):
  battleResult = typeservice.TypeMatch(attack.Types, defend.Types)
  attackGroup = pokemonservice.RarityGroup(attack)
  attackGroup = attackGroup % 7 if attackGroup < 10 else attackGroup
  defendGroup = pokemonservice.RarityGroup(defend)
  defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
  defendLevel = 100 if gymID >= 1000 else 15 if defendGroup == 1 else 25 if defendGroup == 2 else 35 if defendGroup == 3 else 100
  doubleAdv = battleResult >= 2 or (battleResult > 0 and attackLevel > defendLevel*1.5 and attackGroup >= defendGroup)

  if pokemonservice.IsLegendaryPokemon(defend) and len(attack.Types) == 1:
    return battleResult >= 1 and attackGroup >= defendGroup

  return doubleAdv and (attackGroup >= defendGroup or (attackGroup == defendGroup-1 and attackLevel > defendLevel*1.25))

def TeamFight(teamA: list[dict[str, int|PokemonData]], teamB: list[dict[str, int|PokemonData]]):
	fightResults: list[int] = []
	teamAInd = teamBInd = 0
	while teamAInd < len(teamA) and teamBInd < len(teamB):
		teamAFighter = teamA[teamAInd]
		teamBFighter = teamB[teamBInd]
		teamALevel = int(teamAFighter['Level'])
		teamBLevel = int(teamBFighter['Level'])
		teamAGroup = pokemonservice.RarityGroup(teamAFighter['Data'])
		teamAGroup = teamAGroup % 7 if teamAGroup < 10 else teamAGroup
		teamBGroup = pokemonservice.RarityGroup(teamBFighter['Data'])
		teamBGroup = teamBGroup % 7 if teamBGroup < 10 else teamBGroup
		AvBtype = typeservice.TypeMatch(teamAFighter['Data'].Types, teamBFighter['Data'].Types)
		BvAtype = typeservice.TypeMatch(teamBFighter['Data'].Types, teamAFighter['Data'].Types)
		aDoubleAdv = (AvBtype >= 2) or (AvBtype == 2 and len(teamAFighter['Data'].Types) == 1)
		bDoubleAdv = (BvAtype >= 2) or (BvAtype == 2 and len(teamBFighter['Data'].Types) == 1)
		aDoubleDis = (AvBtype < -2) or (AvBtype == -2 and len(teamAFighter['Data'].Types) == 1)
		bDoubleDis = (BvAtype < -2) or (BvAtype == -2 and len(teamBFighter['Data'].Types) == 1)
		AvBrarity = teamAGroup - teamBGroup

		#print(f"{teamAFighter['Data'].Name} - {teamAGroup} - {teamALevel} - {AvBtype}")
		#print(f"{teamBFighter['Data'].Name} - {teamBGroup} - {teamBLevel} - {BvAtype}")

		if AvBtype == -5 or BvAtype == -5:
			aSuccess = 0 if AvBtype == -5 else 1
			bSuccess = 0 if BvAtype == -5 else 1
		#1v10
		elif AvBrarity == -9:
			aSuccess = 1 if aDoubleDis else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 5 if bDoubleDis else 6 if BvAtype <= 0 else 7 if not bDoubleAdv else 8
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2.5) else 1 if teamALevel > (teamBLevel*2) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*0.8) else 0
		#10v1
		elif AvBrarity == 9:
			aSuccess = 5 if aDoubleDis else 6 if AvBtype <= 0 else 7 if not aDoubleAdv else 8
			bSuccess = 1 if bDoubleDis else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*2.5) else 1 if teamBLevel > (teamALevel*2) else 0
		#2v10
		elif AvBrarity == -8:
			aSuccess = 1 if aDoubleDis else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 4 if bDoubleDis else 5 if BvAtype <= 0 else 6 if not bDoubleAdv else 7
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2) else 1 if teamALevel > (teamBLevel*1.5) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.25) else 1 if teamBLevel > (teamALevel*0.7) else 0
		#10v2
		elif AvBrarity == 8:
			aSuccess = 4 if aDoubleDis else 5 if AvBtype <= 0 else 6 if not aDoubleAdv else 7
			bSuccess = 1 if bDoubleDis else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.25) else 1 if teamALevel > (teamBLevel*0.7) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*2) else 1 if teamBLevel > (teamALevel*1.5) else 0
		#3v10
		elif AvBrarity == -7:
			aSuccess = 1 if aDoubleDis else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 2 if bDoubleDis else 3 if BvAtype <= 0 else 4 if not bDoubleAdv else 5
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.75) else 1 if teamALevel > (teamBLevel*1.25) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*0.8) else 0
		#10v3
		elif AvBrarity == 7:
			aSuccess = 2 if aDoubleDis else 3 if AvBtype <= 0 else 4 if not aDoubleAdv else 5
			bSuccess = 1 if bDoubleDis else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.75) else 1 if teamBLevel > (teamALevel*1.25) else 0
		else:
			aSuccess = teamAGroup
			bSuccess = teamBGroup
			aSuccess += 1 if aDoubleDis else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess += 1 if bDoubleDis else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*1.25) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*1.25) else 0

		#print(f"{aSuccess}")
		#print(f"{bSuccess}")

		if aSuccess != bSuccess:
			fightResults.append(1 if aSuccess > bSuccess else 2)
			teamAInd += 1 if aSuccess < bSuccess else 0
			teamBInd += 1 if aSuccess > bSuccess else 0
		elif teamALevel != teamBLevel:
			fightResults.append(1 if teamALevel > teamBLevel else 2)
			teamAInd += 1 if teamALevel < teamBLevel else 0
			teamBInd += 1 if teamALevel > teamBLevel else 0
		elif choice([1,2]) == 1:
			fightResults.append(1)
			teamBInd += 1
		else:
			fightResults.append(2)
			teamAInd += 1
	return fightResults