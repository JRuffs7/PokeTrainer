from random import choice
from models.Pokemon import PokemonData
from models.Trainer import Trainer
from services import pokemonservice, typeservice


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
		AvBrarity = teamAGroup - teamBGroup

		print(f"{teamAFighter['Data'].Name} - {teamAGroup} - {teamALevel} - {AvBtype}")
		print(f"{teamBFighter['Data'].Name} - {teamBGroup} - {teamBLevel} - {BvAtype}")
		#1v10
		if AvBrarity == -9:
			aSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			bSuccess = 0 if AvBtype == -5 else 5 if AvBtype <= -2 else 6 if AvBtype <= 0 else 7 if AvBtype <= 2 else 8
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2.5) else 1 if teamALevel > (teamBLevel*2) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
		#10v1
		elif AvBrarity == 9:
			aSuccess = 0 if AvBtype == -5 else 5 if AvBtype <= -2 else 6 if AvBtype <= 0 else 7 if AvBtype <= 2 else 8
			bSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2.5) else 1 if teamALevel > (teamBLevel*2) else 0
		#2v10
		elif AvBrarity == -8:
			aSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			bSuccess = 0 if AvBtype == -5 else 3 if AvBtype <= -2 else 4 if AvBtype <= 0 else 5 if AvBtype <= 2 else 6
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2) else 1 if teamALevel > (teamBLevel*1.5) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
		#10v2
		elif AvBrarity == 8:
			aSuccess = 0 if AvBtype == -5 else 3 if AvBtype <= -2 else 4 if AvBtype <= 0 else 5 if AvBtype <= 2 else 6
			bSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2) else 1 if teamALevel > (teamBLevel*1.5) else 0
		#3v10
		elif AvBrarity == -7:
			aSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			bSuccess = 0 if AvBtype == -5 else 2 if AvBtype <= -2 else 3 if AvBtype <= 0 else 4 if AvBtype <= 2 else 5
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.75) else 1 if teamALevel > (teamBLevel*1.25) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
		#10v3
		elif AvBrarity == 7:
			aSuccess = 0 if AvBtype == -5 else 2 if AvBtype <= -2 else 3 if AvBtype <= 0 else 4 if AvBtype <= 2 else 5
			bSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.75) else 1 if teamALevel > (teamBLevel*1.25) else 0
		else:
			aSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			bSuccess = 0 if AvBtype == -5 else 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if AvBtype <= 2 else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.75) else 1 if teamALevel > (teamBLevel*1.25) else 0

		if AvBtype == -5:
			aSuccess = 0
		else:
			aSuccess = (AvBtype if AvBtype > 0 else 0) + (5 if teamAGroup == 10 else 0)
			bSuccess = (BvAtype if BvAtype > 0 else 0) + (5 if teamBGroup == 10 else 0)
			aLevelCalc = teamALevel/teamBLevel
			bLevelCalc = teamBLevel/teamALevel
			print(f'{aLevelCalc} - {bLevelCalc}')

		print(f"{aSuccess}")
		print(f"{bSuccess}")

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