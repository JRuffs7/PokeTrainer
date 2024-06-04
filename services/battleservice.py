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
		aDoubleAdv = (AvBtype > 2) or (AvBtype == 2 and len(teamAFighter['Data'].Types) == 1)
		bDoubleAdv = (BvAtype > 2) or (BvAtype == 2 and len(teamBFighter['Data'].Types) == 1)
		aDoubleDis = (AvBtype < -2) or (AvBtype == -2 and len(teamAFighter['Data'].Types) == 1)
		bDoubleDis = (BvAtype < -2) or (BvAtype == -2 and len(teamBFighter['Data'].Types) == 1)
		AvBrarity = teamAGroup - teamBGroup

		print(f"{teamAFighter['Data'].Name} - {teamAGroup} - {teamALevel} - {AvBtype}")
		print(f"{teamBFighter['Data'].Name} - {teamBGroup} - {teamBLevel} - {BvAtype}")
		if AvBtype == -5 or BvAtype == -5:
			aSuccess = 0 if AvBtype == -5 else 1
			bSuccess = 0 if BvAtype == -5 else 1
		#1v10
		if AvBrarity == -9:
			aSuccess = 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 5 if BvAtype <= -2 else 6 if BvAtype <= 0 else 7 if not bDoubleAdv else 8
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2.5) else 1 if teamALevel > (teamBLevel*2) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*0.8) else 0
		#10v1
		elif AvBrarity == 9:
			aSuccess = 5 if AvBtype <= -2 else 6 if AvBtype <= 0 else 7 if not aDoubleAdv else 8
			bSuccess = 1 if BvAtype <= -2 else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*2.5) else 1 if teamBLevel > (teamALevel*2) else 0
		#2v10
		elif AvBrarity == -8:
			aSuccess = 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 3 if BvAtype <= -2 else 4 if BvAtype <= 0 else 5 if not bDoubleAdv else 6
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*2) else 1 if teamALevel > (teamBLevel*1.5) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.25) else 1 if teamBLevel > (teamALevel*0.7) else 0
		#10v2
		elif AvBrarity == 8:
			aSuccess = 4 if AvBtype <= -2 else 5 if AvBtype <= 0 else 6 if not aDoubleAdv else 7
			bSuccess = 1 if BvAtype <= -2 else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.25) else 1 if teamALevel > (teamBLevel*0.7) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*2) else 1 if teamBLevel > (teamALevel*1.5) else 0
		#3v10
		elif AvBrarity == -7:
			aSuccess = 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 2 if BvAtype <= -2 else 3 if BvAtype <= 0 else 4 if not bDoubleAdv else 5
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.75) else 1 if teamALevel > (teamBLevel*1.25) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*0.8) else 0
		#10v3
		elif AvBrarity == 7:
			aSuccess = 3 if aDoubleDis else 4 if AvBtype <= 0 else 5 if not aDoubleAdv else 6
			bSuccess = 1 if bDoubleDis else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*0.8) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.75) else 1 if teamBLevel > (teamALevel*1.25) else 0
		else:
			aSuccess = 1 if AvBtype <= -2 else 2 if AvBtype <= 0 else 3 if not aDoubleAdv else 4
			bSuccess = 1 if BvAtype <= -2 else 2 if BvAtype <= 0 else 3 if not bDoubleAdv else 4
			aSuccess += int(teamALevel/teamBLevel)*2 if teamALevel > (teamBLevel*1.5) else 1 if teamALevel > (teamBLevel*1.25) else 0
			bSuccess += int(teamBLevel/teamALevel)*2 if teamBLevel > (teamALevel*1.5) else 1 if teamBLevel > (teamALevel*1.25) else 0

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