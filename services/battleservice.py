import math
from random import choice
from typing import Tuple
from models.Battle import BattleAction, BattleTurn, CpuBattle
from models.Item import Pokeball
from models.Pokemon import Move, Pokemon, PokemonData
from models.Move import MoveData
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import moveservice, pokemonservice, statservice, trainerservice, typeservice

rechargeMoves = [63, 307, 308, 338, 416, 439, 459, 711, 794, 795]
consecutiveMoves = []

#region Flee

def FleeAttempt(battle: CpuBattle, attempts: int):
	trainerData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamAPkmn.Pokemon_Id)
	cpuData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id)
	if statservice.GenerateStat(battle.TeamAPkmn, trainerData, StatEnum.Speed) >= statservice.GenerateStat(battle.TeamBPkmn, cpuData, StatEnum.Speed):
		return True
	speedCalc = math.floor((statservice.GenerateStat(battle.TeamAPkmn, trainerData, StatEnum.Speed)*32)/(statservice.GenerateStat(battle.TeamBPkmn, cpuData, StatEnum.Speed)/4))
	totalCalc = (speedCalc+30*attempts)/256
	if totalCalc > 255:
		return True
	return choice(range(256)) < totalCalc

#endregion

#region Attack

def TeamAAttackFirst(move1: MoveData, move2: MoveData, battle: CpuBattle):
	if move1.Priority > move2.Priority:
		return True
	elif move1.Priority < move2.Priority:
		return False
	else:
		spdA = statservice.GenerateStat(battle.TeamAPkmn, next(p for p in battle.AllPkmnData if p.Id == battle.TeamAPkmn.Pokemon_Id), StatEnum.Speed)
		spdB = statservice.GenerateStat(battle.TeamBPkmn, next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.Speed)
		if spdA > spdB:
			return True
		elif spdA < spdB:
			return False
		else:
			return choice([1,2]) == 1

def AbleToAttack(battle: CpuBattle, teamA: bool) -> Tuple[bool,str]:
	lastTeamATurn = next((t for t in battle.Turns if t.TeamA), None)
	lastTeamBTurn = next((t for t in battle.Turns if not t.TeamA), None)
	lastTeamATurn2 = next((t for t in battle.Turns if t.TeamA and t != lastTeamATurn), None)
	lastTeamBTurn2 = next((t for t in battle.Turns if not t.TeamA and t != lastTeamBTurn), None)
	if (teamA and lastTeamATurn.Move.Id in rechargeMoves and lastTeamATurn2.Move.Id not in rechargeMoves) or (not teamA and lastTeamBTurn.Move.Id in rechargeMoves and lastTeamBTurn2.Move.Id not in rechargeMoves):
		return False,"Recharging..."
	if (teamA and lastTeamATurn.Move.Id == 117 and lastTeamATurn2.Move.Id != 117) or (not teamA and lastTeamBTurn.Move.Id == 117 and lastTeamBTurn2.Move.Id != 117):
		return False,"Storing Energy..."

def MoveAccuracy(move: Move, attacking: Pokemon, battle: CpuBattle):
	teamA = attacking.Id == battle.TeamAPkmn.Id
	moveData = next(m for m in battle.AllMoveData if m.Id == move.MoveId)
	if not moveData.Accuracy:
		return True
	acc = moveData.Accuracy
	modif = 1
	stgMult = (battle.TeamAAccuracy - battle.TeamBEvasion) if teamA else (battle.TeamBAccuracy - battle.TeamAEvasion)
	stg = (3 + (stgMult if stgMult > 0 else 0))/(3 - (stgMult if stgMult < 0 else 0))
	mBerry = 1
	affection = 0
	return choice(range(1,101)) < (acc*modif*stg*mBerry-affection)

def AttackDamage(move: Move, attacking: Pokemon, defending: Pokemon, battle: CpuBattle):
	attData = next(p for p in battle.AllPkmnData if p.Id == attacking.Pokemon_Id)
	defData = next(p for p in battle.AllPkmnData if p.Id == defending.Pokemon_Id)
	moveData = next(m for m in battle.AllMoveData if m.Id == move.MoveId)
	dmgA = ((2*attacking.Level)/5) + 2
	dmgB = statservice.GenerateStat(attacking, attData, StatEnum.Attack if moveData.AttackType.lower() == 'physical' else StatEnum.SpecialAttack)/statservice.GenerateStat(defending, defData, StatEnum.Defense if moveData.AttackType.lower() == 'physical' else StatEnum.SpecialDefense)
	baseDmg = ((dmgA*(moveData.Power or 0)*dmgB)/50) + 2
	targets = 0.75 if moveData.Targets > 1 else 1
	pb = 1
	weather = 1
	glaive = 2 if ((battle.LastTeamAMove.Id == 862 and attacking.Id == battle.TeamAPkmn.Id) or (battle.LastTeamBMove.Id == 862 and attacking.Id == battle.TeamBPkmn.Id)) else 1
	critical = Critical(move)
	random = choice(range(85,101))/100
	stab = 1.5 if move.MoveType in battle.TeamAData.Types else 1
	typedmg = statservice.TypeDamage(moveData.MoveType, defData.Types)
	burn = 0.5 if attacking.CurrentAilment == 4 and moveData.AttackType.lower() == 'physical' else 1 #burn
	other = ReduceDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id) if critical == 1 else 1
	zmove = 1
	terrashield = 1

	return baseDmg*targets*pb*weather*glaive*critical*random*stab*typedmg*burn*other*zmove*terrashield

def ReduceDamage(moveData: MoveData, battle: CpuBattle, teamA: bool):
	if moveData.AttackType.lower() == 'physical':
		if teamA:
			return 0.5 if battle.TeamBPhysReduce else 1
		else:
			return 0.5 if battle.TeamAPhysReduce else 1
	if moveData.AttackType.lower() == 'special':
		if teamA:
			return 0.5 if battle.TeamBSpecReduce else 1
		else:
			return 0.5 if battle.TeamASpecReduce else 1
	return 1

def Critical(moveData: MoveData):
	if moveData.UniqueDamage:
		return 1
	if moveData.CritRate > 1:
		return 1.5
	critcalc = choice(range(96))
	if moveData.CritRate == 1:
		return 1.5 if critcalc < 12 else 1
	return 1.5 if critcalc in [0,32,64,95] else 1

def ApplyStatus(move: Move, target: Pokemon, battle: CpuBattle):
	targetData = next(p for p in battle.AllPkmnData if p.Id == target.Pokemon_Id)
	moveData = next(m for m in battle.AllMoveData if m.Id == move.MoveId)

#endregion

#region Capture

def TryCapture(pokeball: Pokeball, trainer: Trainer, battle: CpuBattle):
	trainerservice.ModifyItemList(trainer, str(pokeball.Id), -1)
	pkmnData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id)
	capture = False
	#Masterball
	if pokeball.Id == 1:
		capture =  True
	else:
		hpMax = statservice.GenerateStat(battle.TeamBPkmn, pkmnData, StatEnum.HP)
		part1 = ((3*hpMax) - (2*battle.TeamBPkmn.CurrentHP))/(3*hpMax)
		part2 = math.floor(part1*4096*pkmnData.CaptureRate*pokeball.CaptureRate)
		bonusLevel = max(((36 - (2*battle.TeamBPkmn.Level))/10), 1) if battle.TeamBPkmn.Level < 13 else 1
		bonusStatus = 2.5 if battle.TeamBPkmn.CurrentAilment in [2,3] else 1.5 if battle.TeamBPkmn.CurrentAilment in [1,4,5] else 1
		formula = part2*bonusLevel*bonusStatus
		numShakes = 4
		#Sinnoh Reward
		if trainerservice.HasRegionReward(trainer, 4) and choice(range(256)) < round(formula):
			numShakes = 1
		shake = 0
		while shake < numShakes:
			shakeCheck = 65536*(math.pow((formula/1044480),0.1875))
			if choice(range(65536)) < shakeCheck:
				capture = True
			else:
				capture = False
				break
			shake += 1
	
	if capture:
		if len(trainer.Team) >= 6:
			pokemonservice.HealPokemon(battle.TeamBPkmn, pkmnData)
		trainer.OwnedPokemon.append(battle.TeamBPkmn)
		trainerservice.TryAddToPokedex(trainer, pkmnData, battle.TeamBPkmn.IsShiny)
		trainerservice.TryAddMissionProgress(trainer, 'Catch', pkmnData.Types)
		#Paldea Reward
		if trainerservice.HasRegionReward(trainer, 9):
			for p in trainerservice.GetTeam(trainer):
				pokemonservice.AddExperience(
					p, 
					next(t for t in battle.AllPkmnData if t.Id == p.Pokemon_Id), 
					math.floor(pokemonservice.ExpForPokemon(battle.TeamBPkmn, pkmnData, False, battle.TeamAPkmn.Level)/2))
		if len(trainer.Team) < 6:
			trainer.Team.append(battle.TeamBPkmn.Id)
	return capture



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