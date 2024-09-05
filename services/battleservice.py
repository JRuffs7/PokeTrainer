import math
from random import choice
from typing import Tuple
from models.Battle import BattleAction, BattleTurn, CpuBattle
from models.Item import Item, Pokeball, Potion
from models.Pokemon import Move, Pokemon, PokemonData
from models.Move import MoveData
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import moveservice, pokemonservice, statservice, trainerservice, typeservice
from services.utility import battleai


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
		if battle.TeamAPkmn.CurrentAilment == 1: #Paralysis
			spdA = spdA/2
		spdB = statservice.GenerateStat(battle.TeamBPkmn, next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.Speed)
		if battle.TeamBPkmn.CurrentAilment == 1: #Paralysis
			spdB = spdB/2

		if spdA > spdB:
			return True
		elif spdA < spdB:
			return False
		else:
			return choice([1,2]) == 1

def AilmentCheck(pokemon: Pokemon, battle: CpuBattle):
	#Paralysis
	if pokemon.CurrentAilment == 1:
		return choice(range(101)) < 75
	
	#Sleep
	if pokemon.CurrentAilment == 2:
		pkmnTurns = [t for t in battle.Turns if t.PokemonId == pokemon.Id]
		if next((t for t in pkmnTurns if t.PokemonId == pokemon.Id and t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 3)), None):
			pokemon.CurrentAilment = None
			return True
		if next((t for t in pkmnTurns if t.PokemonId == pokemon.Id and t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 2)), None) and choice(range(101))%2 == 0:
			pokemon.CurrentAilment = None
			return True
		if next((t for t in pkmnTurns if t.PokemonId == pokemon.Id and t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 1)), None) and choice(range(101))%2 == 0:
			pokemon.CurrentAilment = None
			return True
		return False
	
	#Freeze
	if pokemon.CurrentAilment == 3 and choice(range(101)) < 20:
		pokemon.CurrentAilment = None
		return True
	
	#Confused
	if pokemon.CurrentAilment == 6:
		if (battle.TeamAConfusion == 0 and pokemon.Id == battle.TeamAPkmn.Id) or (battle.TeamBConfusion == 0 and pokemon.Id == battle.TeamBPkmn.Id):
			pokemon.CurrentAilment = None
			return True
		return choice(range(101)) < 67
	
	#Trap
	if pokemon.CurrentAilment == 8:
		if (battle.TeamATrap == 0 and pokemon.Id == battle.TeamAPkmn.Id) or (battle.TeamBTrap == 0 and pokemon.Id == battle.TeamBPkmn.Id):
			pokemon.CurrentAilment = None
			return True
	return None

def CanChooseAttack(battle: CpuBattle, teamA: bool):
	pkmnTurns = [t for t in battle.Turns if t.TeamA == teamA]
	lastTurn = next((t for t in pkmnTurns), None)
	if not lastTurn:
		return True,BattleAction.Attack
	
	if lastTurn.Action == BattleAction.Charge:
		prevTurn2 = next((t for t in pkmnTurns if t.TurnNum != lastTurn.TurnNum),None)
		return (False,BattleAction.Attack) if prevTurn2 and prevTurn2.Action == BattleAction.Charge else (False,BattleAction.Charge)
	
	if lastTurn.Move and lastTurn.Move.Recharge:
		return False,BattleAction.Recharge
	
	consAttack = battle.TeamAConsAttacks if teamA else battle.TeamBConsAttacks
	if consAttack:
		return False,BattleAction.Attack

	return True,BattleAction.Attack

def MoveAccuracy(move: MoveData, battle: CpuBattle, teamA: bool):
	if (teamA and battle.TeamBImmune) or (not teamA and battle.TeamAImmune):
		return False
	if not move.Accuracy:
		return True
	if move.Id in [12,32,90,329]:
		attacking = battle.TeamAPkmn.Level if teamA else battle.TeamBPkmn
		defending = battle.TeamBPkmn.Level if teamA else battle.TeamAPkmn
		if attacking.Level < defending.Level:
			return False
		acc = 20 if move.Id == 329 and move.MoveType not in next(p for p in battle.AllPkmnData if p.Id == attacking.Pokemon_Id).Types else 30
		acc += (attacking.Level - defending.Level)
		return choice(range(1,101)) < acc

	acc = move.Accuracy
	modif = 1
	stgMult = (battle.TeamAStats['7'] - battle.TeamBStats['8']) if teamA else (battle.TeamBStats['7'] - battle.TeamAStats['8'])
	stg = (3 + (stgMult if stgMult > 0 else 0))/(3 - (stgMult if stgMult < 0 else 0))
	mBerry = 1
	affection = 0
	return choice(range(1,101)) < (acc*modif*stg*mBerry-affection)

def SpecialHitCases(move: MoveData, battle: CpuBattle, userFirst: bool, teamA: bool, teamAAttack: MoveData|None, teamBAttack: MoveData|None):
	pokemon = battle.TeamAPkmn if teamA else battle.TeamBPkmn
	
	if move.Id in [13,19,76,91,130,143,291,340,467,553,554,566,601,669,800,905] and not CheckChargingMove(move.Id, pokemon.Id, battle, 1):
		return BattleAction.Charge
	if move.Id in [68,243] and not CheckCounterMove(move.AttackType.lower(), pokemon.Id, battle):
		return BattleAction.Failed

	if move.Id == 117: 
		if not CheckChargingMove(117, pokemon.Id, battle, 2):
			return BattleAction.Charge
		prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemon.Id and t.TurnNum == battle.CurrentTurn-2),None)
		oppMoves = [t for t in battle.Turns if t.PokemonId != pokemon.Id and battle.Turns.index(t) < battle.Turns.index(prevTurn)]
		if not [m for m in oppMoves if m.DamageDone]:
			return BattleAction.Failed
	if move.Id in [252, 660]: 
		prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemon.Id and t.TurnNum == battle.CurrentTurn-1),None)
		if next((t for t in battle.Turns if t.TurnNum == battle.CurrentTurn),None) or prevTurn or (not teamA and userFirst) or (teamA and not userFirst):
			return BattleAction.Failed
	if move.Id in [368,389,918]: 
		checkattack = teamBAttack if teamA else teamAAttack
		oppMove = next((t for t in battle.Turns if t.PokemonId != pokemon.Id and t.TurnNum == battle.CurrentTurn), None)
		if oppMove or not checkattack or checkattack.AttackType.lower() not in ['physical','special'] or (move.Id == 918 and checkattack.Priority < 1):
			return BattleAction.Failed
	return BattleAction.Attack
	
def CheckCounterMove(attackType: str|None, pokemonId: str, battle: CpuBattle):
	oppMove = next((t for t in battle.Turns if t.PokemonId != pokemonId and t.TurnNum == battle.CurrentTurn), None)
	if not oppMove or oppMove.Action != BattleAction.Attack or not oppMove.DamageDone or not oppMove.Move or (attackType is not None and oppMove.Move.AttackType.lower() != attackType):
		return False
	return True

def CheckChargingMove(moveId: int, pokemonId: str, battle: CpuBattle, numCharges: int):
	for i in range(numCharges,0,-1):
		prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemonId and t.TurnNum == battle.CurrentTurn-i),None)
		if not prevTurn or not prevTurn.Move or prevTurn.Move.Id != moveId or prevTurn.Action != BattleAction.Charge:
			return False
	return True

def SpecialDamage(move: MoveData, battle: CpuBattle, teamA: bool):
	opponent = battle.TeamBPkmn if teamA else battle.TeamAPkmn
	oppData = next(p for p in battle.AllPkmnData if p.Id == opponent.Pokemon_Id)
	effect = typeservice.AttackEffect(move.MoveType, oppData.Types)
	if move.Id == 265 and opponent.CurrentAilment == 1 and effect: #SmellingSalts
		opponent.CurrentAilment = None
		return 2
	if move.Id == 329 and move.MoveType in oppData.Types:
		return 0
	if move.Id == 358 and opponent.CurrentAilment == 2 and effect: #WakeUpSlap
		opponent.CurrentAilment = None
		return 2
	if move.Id == 664 and opponent.CurrentAilment == 4: #SparklingAria
		opponent.CurrentAilment = None
		return 1
	return 1

def AttackDamage(move: MoveData, attacking: Pokemon, defending: Pokemon, battle: CpuBattle):
	typedmg = statservice.TypeDamage(move.MoveType, defData.Types)
	if move.UniqueDamage:
		return UniqueDamage(move, battle, attacking, defending)*(1 if typedmg > 0 else 0)

	if not move.Power:
		return 0
	
	attData = next(p for p in battle.AllPkmnData if p.Id == attacking.Pokemon_Id)
	defData = next(p for p in battle.AllPkmnData if p.Id == defending.Pokemon_Id)
	lastTeamAAttack = next((t for t in battle.Turns if t.TeamA and t.Move), None)
	lastTeamBAttack = next((t for t in battle.Turns if not t.TeamA and t.Move), None)

	dmgA = ((2*attacking.Level)/5) + 2
	if move.AttackType.lower() == 'physical':
		dmgB = statservice.GenerateStat(attacking, attData, StatEnum.Attack)/statservice.GenerateStat(defending, defData, StatEnum.Defense)
	else:
		dmgB = statservice.GenerateStat(attacking, attData, StatEnum.SpecialAttack)/statservice.GenerateStat(defending, defData, StatEnum.SpecialDefense)
	power = (move.Power or 0)*SpecialDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id)
	baseDmg = ((dmgA*power*dmgB)/50) + 2
	targets = 0.75 if move.Targets > 1 else 1
	pb = 1
	weather = 1
	glaive = 2 if ((lastTeamAAttack and lastTeamAAttack.Move.Id == 862 and attacking.Id == battle.TeamAPkmn.Id) or (lastTeamBAttack and lastTeamBAttack.Move.Id == 862 and attacking.Id == battle.TeamBPkmn.Id)) else 1
	critical = Critical(move)
	random = choice(range(85,101))/100
	stab = 1.5 if move.MoveType in attData.Types else 1
	burn = 0.5 if attacking.CurrentAilment == 4 and move.AttackType.lower() == 'physical' else 1 #burn
	other = ReduceDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id) if critical == 1 else 1
	zmove = 1
	terrashield = 1

	damage = baseDmg*targets*pb*weather*glaive*critical*random*stab*typedmg*burn*other*zmove*terrashield
	if damage != 0:
		damage = damage*SpecialDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id)

def ConfusionDamage(pokemon: Pokemon, data: PokemonData):
	dmgA = ((2*pokemon.Level)/5) + 2
	dmgB = statservice.GenerateStat(pokemon, data, StatEnum.Attack)/statservice.GenerateStat(pokemon, data, StatEnum.Defense)
	baseDmg = ((dmgA*40*dmgB)/50) + 2
	random = choice(range(85,101))/100
	pokemon.CurrentHP -= max(round(baseDmg*random), 0)

def AilmentDamage(pokemon: Pokemon, data: PokemonData):
	maxHp = statservice.GenerateStat(pokemon, data, StatEnum.HP)
	match pokemon.CurrentAilment:
		case 4,5: #Burn, Poison
			pokemon.CurrentHP = max(pokemon.CurrentHP - max(round(maxHp/16),1), 0)
		case 8,18: #Trap, Seeding
			pokemon.CurrentHP = max(pokemon.CurrentHP - max(round(maxHp/16),1), 0)

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

def UniqueDamage(moveData: MoveData, battle: CpuBattle, attacking: Pokemon, defending: Pokemon):

	if moveData.Id in [12,32,90,329]:
		return 65535
	if moveData.Id == 49:
		return 20
	if moveData.Id in [68,243,368,894]:
		oppMove = next(t for t in battle.Turns if t.PokemonId == defending.Id and t.TurnNum == battle.CurrentTurn)
		return oppMove.DamageDone*(2 if moveData.Id in [68,243] else 1.5)
	if moveData.Id in [69,101]:
		return attacking.Level
	if moveData.Id == 82:
		return 40
	if moveData.Id == 117:
		firstMove = next(t for t in battle.Turns if t.PokemonId == attacking.Id and t.TurnNum == battle.CurrentTurn-2)
		return 2*sum([t.DamageDone for t in battle.Turns if t.PokemonId == defending.Id and battle.Turns.index(t) < battle.Turns.index(firstMove)])
	if moveData.Id == 149:
		return max(math.floor((attacking.Level*((10*choice(range(101)))+50))/100), 1)
	if moveData.Id in [162,877]:
		return math.floor(defending.CurrentHP/2)
	if moveData.Id == 283:
		return (attacking.CurrentHP - defending.CurrentHP) / 2
	if moveData.Id == 515:
		return attacking.CurrentHP
	return moveData.Power

def ApplyStatus(moveData: MoveData, target: Pokemon, battle: CpuBattle):
	targetData = next(p for p in battle.AllPkmnData if p.Id == target.Pokemon_Id)

#endregion

#region Capture

def TryCapture(pokeball: Pokeball, trainer: Trainer, battle: CpuBattle):
	trainerservice.ModifyItemList(trainer, str(pokeball.Id), -1)
	pkmnData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id)
	capture = False
	#Masterball
	if pokeball.Id == 1:
		capture = True
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

#endregion

#region Turns

def ResetStats(battle: CpuBattle, teamA: bool):
	if teamA:
		battle.TeamAStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
		battle.TeamAConsAttacks = 0
		battle.TeamAConfusion = 0
		if battle.TeamAPkmn.CurrentAilment in [6,8,18]:
			battle.TeamAPkmn.CurrentAilment = None
	else:
		battle.TeamBStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
		battle.TeamBConsAttacks = 0
		battle.TeamBConfusion = 0
		if battle.TeamBPkmn.CurrentAilment in [6,8,18]:
			battle.TeamBPkmn.CurrentAilment = None

def AddTurn(battle: CpuBattle, turnNum: int, teamA: bool, action: BattleAction, move: MoveData|None, damage: int|None):
	battle.Turns.insert(0, BattleTurn.from_dict({
		'TurnNum': turnNum,
		'TeamA': teamA,
		'PokemonId': battle.TeamAPkmn.Id if teamA else battle.TeamBPkmn.Id,
		'Action': action,
		'Move': move,
		'DamageDone': damage
	}))

#endregion

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