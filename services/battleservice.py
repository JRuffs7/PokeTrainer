import math
from random import choice
from models.Battle import BattleAction, BattleTurn, CpuBattle
from models.Item import Item, Pokeball
from models.Pokemon import Pokemon, PokemonData
from models.Move import MoveData
from models.Stat import Stat, StatEnum
from models.Trainer import Trainer
from services import pokemonservice, statservice, trainerservice, typeservice


#region Flee

def FleeAttempt(battle: CpuBattle, attempts: int):
	trainerData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamAPkmn.Pokemon_Id)
	cpuData = next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id)
	teamASpeed = statservice.GenerateStat(battle.TeamAPkmn, trainerData, StatEnum.Speed, battle.TeamAStats)
	teamBSpeed = statservice.GenerateStat(battle.TeamBPkmn, cpuData, StatEnum.Speed, battle.TeamBStats)
	if teamASpeed >= teamBSpeed:
		return True
	speedCalc = math.floor((teamASpeed*32)/(teamBSpeed/4))
	totalCalc = (speedCalc+30*attempts)/256
	return choice(range(256)) < totalCalc

#endregion

#region PreAttack

def GetTurn(battle: CpuBattle, teamA: bool, roundsBefore: int, pokemonId: str|None):
	turns = [t for t in battle.Turns if t.TeamA == teamA]
	if not pokemonId:
		return next((t for t in turns if t.TurnNum == (battle.CurrentTurn - roundsBefore)),None)
	return next((t for t in turns if t.TurnNum == (battle.CurrentTurn - roundsBefore) and t.PokemonId == pokemonId),None)

def TeamAAttackFirst(teamAMove: MoveData|None, teamBMove: MoveData|None, battle: CpuBattle):
	if not teamAMove:
		return True
	if not teamBMove:
		return False
	if teamAMove.Priority > teamBMove.Priority:
		return True
	elif teamAMove.Priority < teamBMove.Priority:
		return False
	else:
		spdA = statservice.GenerateStat(battle.TeamAPkmn, next(p for p in battle.AllPkmnData if p.Id == battle.TeamAPkmn.Pokemon_Id), StatEnum.Speed, battle.TeamAStats)
		if battle.TeamAPkmn.CurrentAilment == 1: #Paralysis
			spdA = spdA/2
		spdB = statservice.GenerateStat(battle.TeamBPkmn, next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.Speed, battle.TeamBStats)
		if battle.TeamBPkmn.CurrentAilment == 1: #Paralysis
			spdB = spdB/2

		if spdA > spdB:
			return True
		elif spdA < spdB:
			return False
		else:
			return choice([1,2]) == 1

def CanChooseAttack(battle: CpuBattle, teamA: bool):
	pkmn = battle.TeamAPkmn if teamA else battle.TeamBPkmn
	turn = GetTurn(battle, teamA, 1, pkmn.Id)
	if not turn:
		return True,BattleAction.Attack
	
	mustLoaf = False
	if pkmn.Pokemon_Id in [287, 289]:
		lastAttack = next((t for t in battle.Turns if t.TeamA == teamA and t.TurnNum < battle.CurrentTurn and t.PokemonId == pkmn.Id and t.Action in [BattleAction.Attack,BattleAction.Charge]),None)
		lastLoaf = next((t for t in battle.Turns if t.TeamA == teamA and t.TurnNum < battle.CurrentTurn and t.PokemonId == pkmn.Id and t.Action in [BattleAction.Loaf,BattleAction.Recharge]),None)
		lastSwap = next((t for t in battle.Turns if t.TeamA == teamA and t.TurnNum < battle.CurrentTurn and t.Action == BattleAction.Swap),None)
		if lastAttack:
			if (lastSwap and lastSwap.TurnNum < lastAttack.TurnNum) or not lastSwap:
				if (lastLoaf and lastLoaf.TurnNum < lastAttack.TurnNum) or not lastLoaf:
					mustLoaf = True

	if turn.Action == BattleAction.Charge:
		if turn.Move.Id in [117,353]:
			turn2 = GetTurn(battle, teamA, 2, turn.PokemonId)
			if not turn2 or turn2.Action != BattleAction.Charge:
				return (False, BattleAction.Charge)
		return (False, BattleAction.Attack) if not mustLoaf else (True, BattleAction.Loaf)
	
	if turn.Move and turn.Move.Recharge:
		return (False,BattleAction.Recharge)
	
	if (teamA and battle.TeamAConsAttacks > 0) or (not teamA and battle.TeamBConsAttacks > 0):
		return (False,BattleAction.Attack) if not mustLoaf else (True, BattleAction.Loaf)

	return (True,BattleAction.Attack) if not mustLoaf else (True,BattleAction.Loaf)

def SpecialHitCases(move: MoveData, battle: CpuBattle, pokemon: Pokemon, opponent: Pokemon, goingFirst: bool, oppAttack: MoveData|None):	
	if move.Healing and pokemon.CurrentHP == statservice.GenerateStat(pokemon, next(p for p in battle.AllPkmnData if p.Id == pokemon.Pokemon_Id), StatEnum.HP):
		return BattleAction.Failed
	match move.Id:
		case 13|19|76|91|130|143|248|291|340|467|553|554|566|601|669|800|905:
			if HasToCharge(move.Id, pokemon.Id, battle, 1):
				return BattleAction.Charge
		case 68|243:
			if not CanCounter(move.AttackType.lower(), opponent.Id, battle):
				return BattleAction.Failed
		case 113:
			if (pokemon.Id == battle.TeamAPkmn.Id and battle.TeamASpecReduce) or (pokemon.Id == battle.TeamBPkmn.Id and battle.TeamBSpecReduce):
				return BattleAction.Failed
		case 115:
			if (pokemon.Id == battle.TeamAPkmn.Id and battle.TeamAPhysReduce) or (pokemon.Id == battle.TeamBPkmn.Id and battle.TeamBPhysReduce):
				return BattleAction.Failed
		case 117,353: 
			if HasToCharge(117, pokemon.Id, battle, 2):
				return BattleAction.Charge
			prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemon.Id and t.TurnNum == battle.CurrentTurn-2),None)
			oppMoves = [t for t in battle.Turns if t.PokemonId != pokemon.Id and battle.Turns.index(t) < battle.Turns.index(prevTurn)]
			if not [m for m in oppMoves if m.DamageDone]:
				return BattleAction.Failed
		case 138|171:
			if opponent.CurrentAilment != 2:
				return BattleAction.Failed
		case 173:
			if pokemon.CurrentAilment != 2:
				return BattleAction.Failed
		case 252|660: 
			prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemon.Id and t.TurnNum == battle.CurrentTurn-1),None)
			if next((t for t in battle.Turns if t.TurnNum == battle.CurrentTurn),None) or prevTurn or not goingFirst:
				return BattleAction.Failed
		case 264:
			oppMove = next((t for t in battle.Turns if t.PokemonId != pokemon.Id and t.TurnNum == battle.CurrentTurn), None)
			if oppMove and oppMove.DamageDone:
				return BattleAction.Failed
		case 283:
			if (pokemon.CurrentHP - opponent.CurrentHP) < 2:
				return BattleAction.Failed
		case 368|389|918: 
			oppMove = next((t for t in battle.Turns if t.PokemonId != pokemon.Id and t.TurnNum == battle.CurrentTurn), None)
			if oppMove or not oppAttack or oppAttack.AttackType.lower() not in ['physical','special'] or (move.Id == 918 and oppAttack.Priority < 1):
				return BattleAction.Failed
		case 445:
			if (pokemon.IsFemale is None or opponent.IsFemale is None or pokemon.IsFemale == opponent.IsFemale):
				return BattleAction.Failed
		case 599:
			if opponent.CurrentAilment != 5:
				return BattleAction.Failed
		case 685:
			if opponent.CurrentAilment not in [1,2,3,4,5]:
				return BattleAction.Failed
		case 694:
			if pokemon.Id == battle.TeamAPkmn.Id:
				if battle.TeamASpecReduce or battle.TeamAPhysReduce:
					return BattleAction.Failed
			else:
				if battle.TeamBSpecReduce or battle.TeamBPhysReduce:
					return BattleAction.Failed
	return BattleAction.Attack
	
def CanCounter(attackType: str|None, pokemonId: str, battle: CpuBattle):
	oppMove = next((t for t in battle.Turns if t.PokemonId == pokemonId and t.TurnNum == battle.CurrentTurn and t.DamageDone), None)
	if (not oppMove) or (not oppMove.Move) or ((attackType is not None) and oppMove.Move.AttackType.lower() != attackType):
		return False
	return True

def HasToCharge(moveId: int, pokemonId: str, battle: CpuBattle, numCharges: int):
	for i in range(numCharges,0,-1):
		prevTurn = next((t for t in battle.Turns if t.PokemonId == pokemonId and t.TurnNum == battle.CurrentTurn-i),None)
		if not prevTurn or not prevTurn.Move or prevTurn.Move.Id != moveId or prevTurn.Action != BattleAction.Charge:
			return True
	return False

def ConfusionDamage(pokemon: Pokemon, data: PokemonData, stats: dict[str,int]):
	dmgA = ((2*pokemon.Level)/5) + 2
	dmgB = statservice.GenerateStat(pokemon, data, StatEnum.Attack, stats)/statservice.GenerateStat(pokemon, data, StatEnum.Defense, stats)
	baseDmg = ((dmgA*40*dmgB)/50) + 2
	random = choice(range(85,101))/100
	damage = min(pokemon.CurrentHP, round(baseDmg*random))
	pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
	return damage

def ConsecutiveAttack(moveData: MoveData, battle: CpuBattle, teamA: bool):
	if not moveData.ConsecutiveAttack:
		return None
	
	if (teamA and battle.TeamAConsAttacks > 0) or (not teamA and battle.TeamAConsAttacks > 0):
		if teamA:
			battle.TeamAConsAttacks -= 1
			return battle.TeamAConsAttacks == 0 and moveData.Id in [37,80,200,833]
		if not teamA:
			battle.TeamBConsAttacks -= 1
			return battle.TeamBConsAttacks == 0 and moveData.Id in []

	numAttacks = 0
	if moveData.Id in [37,80,200,833]:
		numAttacks = choice([1,3])
	if moveData.Id in [205,301]:
		numAttacks = 4
	if moveData.Id in [253]:
		numAttacks = 2

	if teamA:
		battle.TeamAConsAttacks = numAttacks
	else:
		battle.TeamBConsAttacks = numAttacks
	return False

#endregion

#region Ailments

def AilmentCheck(action: BattleAction, pokemon: Pokemon, battle: CpuBattle):
	if action != BattleAction.Attack:
		return None
	match pokemon.CurrentAilment:
		#Paralysis
		case 1:
			return choice(range(100)) < 75
		#Sleep
		case 2:
			pkmnTurns = [t for t in battle.Turns if t.PokemonId == pokemon.Id]
			if next((t for t in pkmnTurns if t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 3)), None):
				return True
			if next((t for t in pkmnTurns if t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 2)), None) and choice(range(100))%2 == 0:
				return True
			if next((t for t in pkmnTurns if t.Action == BattleAction.Sleep and t.TurnNum == (battle.CurrentTurn - 1)), None) and choice(range(100))%2 == 0:
				return True
			return False
		#Freeze
		case 3:
			if choice(range(100)) < 20:
				return True
			return False
		#Confused
		case 6:
			if (battle.TeamAConfusion == 0 and pokemon.Id == battle.TeamAPkmn.Id) or (battle.TeamBConfusion == 0 and pokemon.Id == battle.TeamBPkmn.Id):
				return True
			return choice(range(100)) < 67
		#Trap
		case 8:
			if (battle.TeamATrap == 0 and pokemon.Id == battle.TeamAPkmn.Id) or (battle.TeamBTrap == 0 and pokemon.Id == battle.TeamBPkmn.Id):
				return True
		case _:
			return None

def AilmentDamage(pokemon: Pokemon, data: PokemonData, targetPokemon: Pokemon, targetData: PokemonData):
	maxHp = statservice.GenerateStat(pokemon, data, StatEnum.HP)
	damage = 0
	match pokemon.CurrentAilment:
		case 4: #Burn
			damage = min(pokemon.CurrentHP, max(round(maxHp/16),1))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		case 5|8: #Poison, Trap
			damage = min(pokemon.CurrentHP, max(round(maxHp/8),1))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		case 18: #Seeding
			damage = min(pokemon.CurrentHP, max(round(maxHp/8),1))
			targetPokemon.CurrentHP = min(targetPokemon.CurrentHP + damage, statservice.GenerateStat(targetPokemon, targetData, StatEnum.HP))
	return damage

def ApplyAilment(battle: CpuBattle, moveData: MoveData, target: Pokemon, targetData: PokemonData):
	if not moveData.Ailment or moveData.Ailment == target.CurrentAilment:
		return None
	
	if( (moveData.Ailment == 1 and 13 in targetData.Types) or 
		  (moveData.Ailment == 3 and 15 in targetData.Types) or 
			(moveData.Ailment == 4 and 10 in targetData.Types) or
			(moveData.Ailment == 5 and (4 in targetData.Types or 9 in targetData.Types))
	  ):
		return None
	
	teamA = target.Id == battle.TeamBPkmn.Id
	if moveData.AilmentChance in [0, 100] or choice(range(100)) < moveData.AilmentChance:
		target.CurrentAilment = moveData.Ailment
		if moveData.Ailment == 6 and teamA:
			battle.TeamBConfusion = choice([2,3,4,5])
		if moveData.Ailment == 6 and not teamA:
			battle.TeamAConfusion = choice([2,3,4,5])
		elif moveData.Ailment == 8 and teamA:
			battle.TeamBTrapId = moveData.Id
			battle.TeamBTrap = choice([4,5])
		elif moveData.Ailment == 8 and not teamA:
			battle.TeamATrapId = moveData.Id
			battle.TeamATrap = choice([4,5])
		return statservice.GetAilmentGainedMessage(target, targetData, moveData.Name)
	return None

#endregion

#region Attack

def MoveAccuracy(move: MoveData, battle: CpuBattle, teamA: bool):
	if (teamA and battle.TeamBImmune) or ((not teamA) and battle.TeamAImmune):
		return False
	if not move.Accuracy:
		return True
	if move.Id in [12,32,90,329]:
		attacking = battle.TeamAPkmn if teamA else battle.TeamBPkmn
		defending = battle.TeamBPkmn if teamA else battle.TeamAPkmn
		if attacking.Level < defending.Level:
			return False
		acc = 20 if move.Id == 329 and move.MoveType not in next(p for p in battle.AllPkmnData if p.Id == attacking.Pokemon_Id).Types else 30
		acc += (attacking.Level - defending.Level)
		return choice(range(100)) < acc

	acc = move.Accuracy
	modif = 1
	stgMult = (battle.TeamAStats['7'] - (0 if move.Id == 533 else battle.TeamBStats['8'])) if teamA else (battle.TeamBStats['7'] - (0 if move.Id == 533 else battle.TeamAStats['8']))
	stg = (3 + (stgMult if stgMult > 0 else 0))/(3 - (stgMult if stgMult < 0 else 0))
	mBerry = 1
	affection = 0
	return choice(range(100)) < (acc*modif*stg*mBerry-affection)

def SpecialDamage(move: MoveData, battle: CpuBattle, teamA: bool):
	pokemon = battle.TeamAPkmn if teamA else battle.TeamBPkmn
	opponent = battle.TeamBPkmn if teamA else battle.TeamAPkmn
	oppData = next(p for p in battle.AllPkmnData if p.Id == opponent.Pokemon_Id)
	effect = typeservice.AttackEffect(move.MoveType, oppData.Types)
	match move.Id:
		case 263:
			if pokemon.CurrentAilment in [1,4,5]:
				return 2
		case 265:
			if opponent.CurrentAilment == 1 and effect: #SmellingSalts
				opponent.CurrentAilment = None
				return 2
		case 329:
			if move.MoveType in oppData.Types:
				return 0
		case 358:
			if opponent.CurrentAilment == 2 and effect: #WakeUpSlap
				opponent.CurrentAilment = None
				return 2
		case 506:
			if opponent.CurrentAilment in [1,2,3,4,5]:
				return 2
		case 664:
			if opponent.CurrentAilment == 4: #SparklingAria
				opponent.CurrentAilment = None
				return 1
		case 808:
			oppturn = GetTurn(battle, (not teamA), 0, opponent.Id)
			if oppturn and oppturn.Move and oppturn.Move.StatEffectOpponent and oppturn.Move.StatChanges:
				return 2
	return 1

def UniqueDamage(moveData: MoveData, battle: CpuBattle, attacking: Pokemon, defending: Pokemon):
	match moveData.Id:
		case 12|32|90|329:
			return 65535
		case 49:
			return 20
		case 68|243|368|894:
			oppMove = next((t for t in battle.Turns if t.PokemonId == defending.Id and t.TurnNum == battle.CurrentTurn),None)
			return 0 if not oppMove else (oppMove.DamageDone or 1)*(2 if moveData.Id in [68,243] else 1.5)
		case 69|101:
			return attacking.Level
		case 82:
			return 40
		case 117:
			firstMove = next((t for t in battle.Turns if t.PokemonId == attacking.Id and t.TurnNum == battle.CurrentTurn-2), None)
			return 0 if not firstMove else 2*sum([t.DamageDone for t in battle.Turns if t.DamageDone and t.PokemonId == defending.Id and battle.Turns.index(t) < battle.Turns.index(firstMove)])
		case 149:
			return max(math.floor((attacking.Level*((10*choice(range(100)))+50))/100), 1)
		case 162|877:
			return math.floor(defending.CurrentHP/2)
		case 171:
			return math.floor(statservice.GenerateStat(defending, next(p for p in battle.AllPkmnData if p.Id == defending.Pokemon_Id), StatEnum.HP)/4)
		case 283:
			return (attacking.CurrentHP - defending.CurrentHP) / 2
		case 515:
			return attacking.CurrentHP
		case _:
			return moveData.Power or 0

def AttackDamage(move: MoveData, attacking: Pokemon, defending: Pokemon, battle: CpuBattle):
	attData = next(p for p in battle.AllPkmnData if p.Id == attacking.Pokemon_Id)
	defData = next(p for p in battle.AllPkmnData if p.Id == defending.Pokemon_Id)
	attStats = battle.TeamAStats if attacking.Id == battle.TeamAPkmn.Id and move.Id != 492 else battle.TeamBStats
	defStats = battle.TeamBStats if attacking.Id == battle.TeamAPkmn.Id else battle.TeamAStats
	typedmg = statservice.TypeDamage(move.MoveType, defData.Types)
	if defending.Pokemon_Id == 292 and typedmg < 2:
		typedmg = 0
	if move.UniqueDamage:
		damage = round(UniqueDamage(move, battle, attacking, defending)*(1 if typedmg > 0 else 0))
		damage = min(defending.CurrentHP, damage)
		defending.CurrentHP = max(defending.CurrentHP - damage, 0)
		return damage,False

	if not move.Power and move.Id not in [67,175,360,484,486, 535]:
		return 0,False
	
	lastTeamAAttack = next((t for t in battle.Turns if t.TeamA and t.Move), None)
	lastTeamBAttack = next((t for t in battle.Turns if not t.TeamA and t.Move), None)

	critical = Critical(move)
	dmgA = ((2*attacking.Level)/5) + 2
	if move.AttackType.lower() == 'physical':
		attMo = {} if (critical > 1) and (attStats[str(StatEnum.Attack.value)] < 0) else attStats
		defMo = {} if (move.Id == 533) or ((critical > 1) and (defStats[str(StatEnum.Defense.value)] > 0)) else defStats
		attSt = statservice.GenerateStat(attacking, attData, StatEnum.Attack, attMo)
		defSt = statservice.GenerateStat(defending, defData, StatEnum.Defense, defMo)
	else:
		attMo = {} if (critical > 1) and (attStats[str(StatEnum.Attack.value)] < 0) else attStats
		defMo = {} if (critical > 1) and (defStats[str(StatEnum.Defense.value)] > 0) else defStats
		attSt = statservice.GenerateStat(attacking, attData, StatEnum.SpecialAttack, attMo)
		defSt = statservice.GenerateStat(defending, defData, StatEnum.SpecialDefense, defMo)
	dmgB = attSt/defSt
	power = CalcPower(move, battle, attacking, attData, defending, defData)*SpecialDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id)
	baseDmg = ((dmgA*power*dmgB)/50) + 2
	targets = 0.75 if move.Targets > 1 else 1
	pb = 1
	weather = 1
	glaive = 2 if ((lastTeamAAttack and lastTeamAAttack.Move and lastTeamAAttack.Move.Id == 862 and attacking.Id == battle.TeamAPkmn.Id) or (lastTeamBAttack and lastTeamBAttack.Move and lastTeamBAttack.Move.Id == 862 and attacking.Id == battle.TeamBPkmn.Id)) else 1
	random = choice(range(85,101))/100
	stab = 1.5 if move.MoveType in attData.Types else 1
	burn = 0.5 if attacking.CurrentAilment == 4 and move.AttackType.lower() == 'physical' else 1 #burn
	other = ReduceDamage(move, battle, attacking.Id == battle.TeamAPkmn.Id) if critical == 1 else 1
	zmove = 1
	terrashield = 1

	damage = baseDmg*targets*pb*weather*glaive*critical*random*stab*typedmg*burn*other*zmove*terrashield
	damage = min(defending.CurrentHP, round(damage))
	defending.CurrentHP = max(defending.CurrentHP - damage, 0)
	return damage,critical>1

def CalcPower(move: MoveData, battle: CpuBattle, attack: Pokemon, attackData: PokemonData, defend: Pokemon, defendData: PokemonData):
	teamA = attack.Id == battle.TeamAPkmn.Id
	userStats = battle.TeamAStats if teamA else battle.TeamBStats
	targetStats = battle.TeamBStats if teamA else battle.TeamAStats
	effect = typeservice.AttackEffect(move.MoveType, defendData.Types)
	power = move.Power or 0
	match move.Id:
		case 67:
			weight = defendData.Weight/10
			return 20 if weight < 10 else 40 if weight < 25 else 60 if weight < 50 else 80 if weight < 100 else 100 if weight < 200 else 120
		case 175:
			prcntHPLeft = attack.CurrentHP / statservice.GenerateStat(attack, attackData, StatEnum.HP)
			return 200 if prcntHPLeft < 4.2 else 150 if prcntHPLeft < 10.4 else 100 if prcntHPLeft < 20.8 else 80 if prcntHPLeft < 35.4 else 40 if prcntHPLeft < 68.8 else 20
		case 323:
			return power * attack.CurrentHP / statservice.GenerateStat(attack, attackData, StatEnum.HP)
		case 535:
			prcntWeight = (defend.Weight * 100) / attack.Weight
			return 120 if prcntWeight <= 20 else 100 if prcntWeight <= 25 else 80 if prcntWeight <= 33.34 else 60 if prcntWeight <= 50 else 40
		case 205|301:
			return power * math.pow(2,(5-(battle.TeamAConsAttacks if teamA else battle.TeamBConsAttacks)))
		case 263:
			if attack.CurrentAilment in [1,4,5]:
				return power * 2
		case 265:
			if defend.CurrentAilment == 1 and effect: #SmellingSalts
				defend.CurrentAilment = None
				return power * 2
		case 329:
			if move.MoveType in defendData.Types:
				return 0
		case 358:
			if defend.CurrentAilment == 2 and effect: #WakeUpSlap
				defend.CurrentAilment = None
				return power * 2
		case 360:
			targetSpeed = statservice.GenerateStat(defend, defendData, StatEnum.Speed, targetStats)
			if defend.CurrentAilment == 1: #Paralysis
				targetSpeed = targetSpeed/2
			userSpeed = statservice.GenerateStat(attack, attackData, StatEnum.Speed, userStats)
			if attack.CurrentAilment == 1: #Paralysis
				userSpeed = userSpeed/2
			power = ((25*max(targetSpeed,1))/max(userSpeed,1))+1
			return min(150,int(power))
		case 386:
			targetStats = battle.TeamAStats if attack.Id == battle.TeamBPkmn.Id else battle.TeamBStats
			increase = 0
			for st in targetStats:
				increase += (targetStats[st] if targetStats[st] > 0 else 0)
			return min(200,(60 + (20*increase)))
		case 484:
			weightDiff = defendData.Weight/attackData.Weight*100
			return 40 if weightDiff > 50 else 60 if weightDiff > 33.34 else 80 if weightDiff > 25 else 100 if weightDiff > 20 else 120
		case 486:
			targetStats = battle.TeamAStats[str(StatEnum.Speed.value)] if attack.Id == battle.TeamBPkmn.Id else battle.TeamBStats[str(StatEnum.Speed.value)]
			userStats = battle.TeamBStats[str(StatEnum.Speed.value)] if attack.Id == battle.TeamBPkmn.Id else battle.TeamAStats[str(StatEnum.Speed.value)]
			targetSpeed = statservice.GenerateStat(defend, defendData, StatEnum.Speed, targetStats)
			if defend.CurrentAilment == 1: #Paralysis
				targetSpeed = targetSpeed/2
			userSpeed = statservice.GenerateStat(attack, attackData, StatEnum.Speed, userStats)
			if attack.CurrentAilment == 1: #Paralysis
				userSpeed = userSpeed/2
			speedComp = targetSpeed/userSpeed*100
			if speedComp < 0.01 or speedComp > 100:
				return 40
			return 150 if speedComp <= 25 else 120 if speedComp <= 33.33 else 80 if speedComp <= 50 else 60
		case 506:
			if defend.CurrentAilment in [1,2,3,4,5]:
				return power * 2
		case 664:
			if defend.CurrentAilment == 4: #SparklingAria
				defend.CurrentAilment = None
				return power * 1
		case 808:
			oppturn = GetTurn(battle, (not teamA), 0, defend.Id)
			if oppturn and oppturn.Move and oppturn.Move.StatEffectOpponent and oppturn.Move.StatChanges:
				return power * 2
		case _:
			return power
	return power

def ReduceDamage(moveData: MoveData, battle: CpuBattle, teamA: bool):
	if moveData.AttackType.lower() == 'physical':
		if teamA:
			return 0.5 if battle.TeamBPhysReduce > 0 else 1
		else:
			return 0.5 if battle.TeamAPhysReduce > 0 else 1
	if moveData.AttackType.lower() == 'special':
		if teamA:
			return 0.5 if battle.TeamBSpecReduce > 0 else 1
		else:
			return 0.5 if battle.TeamASpecReduce > 0 else 1
	return 1

def Critical(moveData: MoveData):
	if moveData.UniqueDamage or moveData.CritRate == 0 or moveData.Id == 175:
		return 1
	if moveData.CritRate > 1:
		return 1.5
	critcalc = choice(range(95))
	if moveData.CritRate == 1:
		return 1.5 if critcalc < 12 else 1
	return 1.5 if critcalc in [0,32,64,95] else 1

#endregion

#region PostAttack

def SelfDamage(move: MoveData, pokemon: Pokemon, data: PokemonData):
	match move.Id:
		#Instant KO
		case 120|153|262|515|802:
			damage = pokemon.CurrentHP
			pokemon.CurrentHP = 0
		#Half HP
		case 26|136|720|835|853|916:
			damage = min(pokemon.CurrentHP, round(statservice.GenerateStat(pokemon, data, StatEnum.HP)/2))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		#Half Current HP
		case 796,10007:
			damage = min(pokemon.CurrentHP, round(pokemon.CurrentHP/2))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		#Third HP
		case 775:
			damage = min(pokemon.CurrentHP, round(statservice.GenerateStat(pokemon, data, StatEnum.HP)/3))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		#Quarter HP
		case 165:
			damage = min(pokemon.CurrentHP, round(statservice.GenerateStat(pokemon, data, StatEnum.HP)/4))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		#Sixteenth HP
		case 10001:
			damage = min(pokemon.CurrentHP, round(statservice.GenerateStat(pokemon, data, StatEnum.HP)/16))
			pokemon.CurrentHP = max(pokemon.CurrentHP - damage, 0)
		case _:
			damage = 0
	return abs(damage)

def MoveDrain(moveData: MoveData, pokemon: Pokemon, data: PokemonData, damage: int):
	if moveData.Id in [120,153,262,515,802]:
		pokemon.CurrentHP = 0
		return None
	
	maxHp = statservice.GenerateStat(pokemon, data, StatEnum.HP)
	heal = 0
	if moveData.Healing:
		heal = min(max*(moveData.Healing/100), maxHp - pokemon.CurrentHP)
	if moveData.Drain > 0:
		heal = min(math.floor(damage*(moveData.Drain/100)), maxHp - pokemon.CurrentHP)
	if heal:
		pokemon.CurrentHP += heal
		return f'{pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)} regained **{heal}** HP!'
	
	recoil = min(abs(math.floor(damage*(moveData.Drain/100))), pokemon.CurrentHP)
	if recoil:
		pokemon.CurrentHP -= recoil
		return f'{pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)} took **{recoil}** recoil damage!'

def ApplyStatChange(moveData: MoveData, battle: CpuBattle, teamA: bool):
	if not moveData.StatChanges:
		return None

	if choice(range(100)) >= (moveData.StatChance or 100):
		return None
	
	if teamA:
		targetPkmn = battle.TeamBPkmn if moveData.StatEffectOpponent else battle.TeamAPkmn
		targetStats = battle.TeamBStats if moveData.StatEffectOpponent else battle.TeamAStats
	else:
		targetPkmn = battle.TeamAPkmn if moveData.StatEffectOpponent else battle.TeamBPkmn
		targetStats = battle.TeamAStats if moveData.StatEffectOpponent else battle.TeamBStats
	pkmnData = next(p for p in battle.AllPkmnData if p.Id == targetPkmn.Pokemon_Id)
	increase: list[Stat] = []
	increaseSharp: list[Stat] = []
	decrease: list[Stat] = []
	decreaseSharp: list[Stat] = []
	noChange: list[Stat] = []
	for stat in moveData.StatChanges:
		if (moveData.StatChanges[stat] < 0 and targetStats[stat] == -6) or (moveData.StatChanges[stat] > 0 and targetStats[stat] == 6):
			noChange.append(statservice.GetStat(int(stat)))
		elif moveData.StatChanges[stat] >= 2:
			targetStats[stat] = min(targetStats[stat] + moveData.StatChanges[stat], 6)
			increaseSharp.append(statservice.GetStat(int(stat)))
		elif moveData.StatChanges[stat] > 0:
			targetStats[stat] = min(targetStats[stat] + moveData.StatChanges[stat], 6)
			increase.append(statservice.GetStat(int(stat)))
		elif moveData.StatChanges[stat] <= -2:
			targetStats[stat] = max(targetStats[stat] + moveData.StatChanges[stat], -6)
			decreaseSharp.append(statservice.GetStat(int(stat)))
		elif moveData.StatChanges[stat] < 0:
			targetStats[stat] = max(targetStats[stat] + moveData.StatChanges[stat], -6)
			decrease.append(statservice.GetStat(int(stat)))

	increaseStr = f"{pokemonservice.GetPokemonDisplayName(targetPkmn, pkmnData, False, False)}'s **{'/'.join([s.Name for s in increase])}** went up!" if increase else None
	increaseSharpStr = f"{pokemonservice.GetPokemonDisplayName(targetPkmn, pkmnData, False, False)}'s **{'/'.join([s.Name for s in increaseSharp])}** sharply went up!" if increaseSharp else None
	decreaseStr = f"{pokemonservice.GetPokemonDisplayName(targetPkmn, pkmnData, False, False)}'s **{'/'.join([s.Name for s in decrease])}** went down!" if decrease else None
	decreaseSharpStr = f"{pokemonservice.GetPokemonDisplayName(targetPkmn, pkmnData, False, False)}'s **{'/'.join([s.Name for s in decreaseSharp])}** sharply went down!" if decreaseSharp else None
	noChangeStr = f"{pokemonservice.GetPokemonDisplayName(targetPkmn, pkmnData, False, False)}'s **{'/'.join([s.Name for s in noChange])}** had no change!" if noChange else None

	return [s for s in [increaseStr, increaseSharpStr, decreaseStr, decreaseSharpStr, noChangeStr] if s]

#endregion

#region Capture

def TryCapture(pokeball: Pokeball, trainer: Trainer, battle: CpuBattle, ditto: bool):
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
		if ditto:
			pkmnData = pokemonservice.GetPokemonById(132)
			battle.TeamBPkmn = pokemonservice.GenerateSpawnPokemon(pkmnData, battle.TeamBPkmn.Level, trainerservice.GetShinyOdds(trainer))

		if len(trainer.Team) >= 6:
			pokemonservice.HealPokemon(battle.TeamBPkmn, pkmnData)
		battle.TeamBPkmn.CaughtBy = pokeball.Id
		trainer.OwnedPokemon.append(battle.TeamBPkmn)
		trainerservice.TryAddToPokedex(trainer, pkmnData, battle.TeamBPkmn.IsShiny)
		trainerservice.TryAddMissionProgress(trainer, 'Catch', pkmnData.Types)
		#Paldea Reward
		if trainerservice.HasRegionReward(trainer, 9):
			for p in trainerservice.GetTeam(trainer):
				pokemonservice.AddExperience(
					p, 
					next(t for t in battle.AllPkmnData if t.Id == p.Pokemon_Id), 
					math.floor(pokemonservice.ExpForPokemon(battle.TeamBPkmn, pkmnData, True, False, battle.TeamAPkmn.Level)/4))
		if len(trainer.Team) < 6 and battle.TeamBPkmn.Pokemon_Id != 132:
			trainer.Team.append(battle.TeamBPkmn.Id)
	return capture

#endregion

#region Turns

def CreateTurn(turn: int, teamA: bool, pokemonId: str, action: BattleAction|None = None, move: MoveData|None = None, item: Item|None = None, itemUse: str|None = None):
	return BattleTurn.from_dict({
		'TurnNum': turn,
		'TeamA': teamA,
		'PokemonId': pokemonId,
		'Action': action,
		'Move': move,
		'DamageDone': None,
		'ItemUsed': item,
		'ItemUsedOnId': itemUse
	})

def ResetStats(battle: CpuBattle, teamA: bool):
	if teamA:
		battle.TeamAStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
		battle.TeamAConsAttacks = 0
		battle.TeamAConfusion = 0
		battle.TeamATrap = 0
		battle.TeamATrapId = None
		if battle.TeamAPkmn.CurrentAilment in [6,8,18]:
			battle.TeamAPkmn.CurrentAilment = None
	else:
		battle.TeamBStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
		battle.TeamBConsAttacks = 0
		battle.TeamBConfusion = 0
		battle.TeamBTrap = 0
		battle.TeamBTrapId = None
		if battle.TeamBPkmn.CurrentAilment in [6,8,18]:
			battle.TeamBPkmn.CurrentAilment = None

def AddTurn(battle: CpuBattle, teamA: bool, action: BattleAction, move: MoveData|None, damage: int|None):
	battle.Turns.insert(0, BattleTurn.from_dict({
		'TurnNum': battle.CurrentTurn,
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