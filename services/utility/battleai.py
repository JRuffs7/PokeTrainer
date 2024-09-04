from random import choice
from models.Battle import BattleAction, CpuBattle
from models.Move import MoveData
from models.Pokemon import Pokemon, Move
from models.Stat import StatEnum
from services import battleservice, moveservice, statservice, typeservice


def CpuAction(battle: CpuBattle, cpuTeam: list[Pokemon]):
	if battle.IsWild:
		return BattleAction.Attack,ChooseAttack(battle)
	
	lastUserTurn = next((t for t in battle.Turns if t.TeamA), None)
	#Free Turn, Heal or Attack
	if lastUserTurn and lastUserTurn.Move and lastUserTurn.Move.Recharge:
		item = ShouldUseItem(battle, cpuTeam)
		if item:
			return BattleAction.Item,item
		return BattleAction.Attack,ChooseAttack(battle)
		
	swap = ShouldSwitchPokemon(battle, cpuTeam)
	if swap:
		return BattleAction.Swap,swap
	item = ShouldUseItem(battle, cpuTeam)
	if item:
		return BattleAction.Item,item
	return BattleAction.Attack,ChooseAttack(battle)


def ShouldSwitchPokemon(battle: CpuBattle, cpuTeam: list[Pokemon]):
	if len(cpuTeam) == 1:
		return None
	if next((t for t in battle.Turns if not t.TeamA),None) and next(t for t in battle.Turns if not t.TeamA).Action == BattleAction.Swap:
		return None
	validSwaps = [p for p in cpuTeam if p.Id != battle.TeamBPkmn.Id and p.CurrentHP > (statservice.GenerateStat(p, next(po for po in battle.AllPkmnData if po.Id == p.Pokemon_Id), StatEnum.HP)/3) and p.CurrentAilment not in [1,2,3]]
	if not validSwaps:
		return None
	
	#Pokemon is about to kill the opponent
	if statservice.GenerateStat(battle.TeamBPkmn, next(po for po in battle.AllPkmnData if po.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.Speed) > statservice.GenerateStat(battle.TeamAPkmn, next(po for po in battle.AllPkmnData if po.Id == battle.TeamAPkmn.Pokemon_Id), StatEnum.Speed):
		for m in battle.TeamBPkmn.LearnedMoves:
			mData = next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId)
			if m.PP == 0 or not mData.Power:
				pass
			simAttack = battleservice.AttackDamage(mData, battle.TeamBPkmn, battle.TeamAPkmn, battle)
			if simAttack > battle.TeamAPkmn.CurrentHP:
				return None

	if max([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Priority for m in battle.TeamBPkmn.LearnedMoves]) > max([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Priority for m in battle.TeamAPkmn.LearnedMoves]):
		for m in [mov for mov in battle.TeamBPkmn.LearnedMoves if next(mo for mo in battle.AllMoveData if mo.Id == mov.MoveId).Priority == max([next(mo for mo in battle.AllMoveData if mo.Id == mv.MoveId).Priority for mv in battle.TeamBPkmn.LearnedMoves])]:
			mData = next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId)
			if mData.Power:
				simAttack = battleservice.AttackDamage(next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId), battle.TeamBPkmn, battle.TeamAPkmn, battle)
				if simAttack > battle.TeamAPkmn.CurrentHP:
					return None


	tookDamage = battle.TeamBPkmn.CurrentHP < statservice.GenerateStat(battle.TeamBPkmn, next(po for po in battle.AllPkmnData if po.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.HP)

	#Danger from moves
	levelDiff = battle.TeamBPkmn.Level - battle.TeamAPkmn.Level
	attMoves = [m for m in battle.TeamAPkmn.LearnedMoves if (next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Power or 0) > 70]
	maxEff = [{ 'Data': next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId), 'Effect': typeservice.AttackEffect(m, next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id).Types) } for m in attMoves] if attMoves else []
	superEffectMoves = [m for m in maxEff if m['Effect'] >= 2]
	highPowerSuper = [m for m in superEffectMoves if m['Data'].Power >= 90]
	if tookDamage and -5<levelDiff<5 and superEffectMoves and choice(range(101)) < (50 if highPowerSuper else 25):
		return BestSwapChoice(battle.TeamAPkmn, validSwaps, battle)

	#Danger from status/stats
	if battle.TeamBPkmn.CurrentAilment in [1,2,3,6] or battle.TeamBStats['7'] < -5 or battle.TeamBStats['8'] < -5:
		return BestSwapChoice(battle.TeamAPkmn, validSwaps, battle)
	return None

def BestSwapChoice(opponent: Pokemon, options: list[Pokemon], battle: CpuBattle):
	data = battle.AllPkmnData
	moveData = battle.AllMoveData
	oppData = next(p for p in data if p.Id == opponent.Pokemon_Id)
	selectedPokemon = None
	selectedValue = 0
	for p in options:
		newValue = 0
		pData = next(po for po in data if po.Id == p.Pokemon_Id)
		spdA = statservice.GenerateStat(opponent, oppData, StatEnum.Speed)
		spdB = statservice.GenerateStat(p, pData, StatEnum.Speed)

		for m in [mo for mo in opponent.LearnedMoves if mo.PP > 0]:
			mData = next(mo for mo in moveData if mo.Id == m.MoveId)
			if mData.Power:
				simAttack = battleservice.AttackDamage(mData, opponent, p, battle)
				if simAttack > p.CurrentHP:
					newValue -= 100
				elif simAttack > p.CurrentHP/2 and (mData.Priority > max([next(mov for mov in moveData if mov.Id == mo.MoveId).Priority for mo in p.LearnedMoves if m.PP > 0]) or spdA >= spdB):
					newValue -= 50
				else:
					newValue += (4 - typeservice.AttackEffect(mData.MoveType, pData.Types))
			else:
				newValue += (4 - typeservice.AttackEffect(mData.MoveType, pData.Types))

		if newValue > (2*len(opponent.LearnedMoves)):
			newValue += (p.Level - opponent.Level)/2 if p.Level < opponent.Level else (p.Level - opponent.Level)
		else:
			newValue += (p.Level - opponent.Level) if p.Level < opponent.Level else (p.Level - opponent.Level)/2

		for m in [mo for mo in p.LearnedMoves if mo.PP > 0]:
			newValue += typeservice.AttackEffect(next(mo for mo in moveData if mo.Id == m.MoveId).MoveType, oppData.Types)
		
		newValue += statservice.GenerateStat(p, pData, StatEnum.HP)
		newValue += statservice.GenerateStat(p, pData, StatEnum.Attack)
		newValue += statservice.GenerateStat(p, pData, StatEnum.Defense)
		newValue += statservice.GenerateStat(p, pData, StatEnum.SpecialAttack)
		newValue += statservice.GenerateStat(p, pData, StatEnum.SpecialDefense)
		newValue += statservice.GenerateStat(p, pData, StatEnum.Speed)

		newValue -= (5 if p.CurrentAilment in [4,5] else 0)

		if newValue > selectedValue:
			selectedPokemon = p
			selectedValue = newValue
	return selectedPokemon
		
def ShouldUseItem(battle: CpuBattle, team: list[Pokemon]):
	if len([t for t in battle.Turns if t.Action == BattleAction.Item and not t.TeamA]) == 3:
		return None
	if next((t for t in battle.Turns if not t.TeamA),None) and next(t for t in battle.Turns if not t.TeamA).Action == BattleAction.Item:
		return None
	
	availablePkmn = [p for p in team if p.CurrentHP > 0 and (p.CurrentAilment or p.CurrentHP < (statservice.GenerateStat(p, next(po for po in battle.AllPkmnData if po.Id == p.Pokemon_Id), StatEnum.HP)/2))]
	if not availablePkmn:
		return None
	
	selectedPokemon = battle.TeamBPkmn
	selectedValue = 0
	for p in availablePkmn:
		newValue = p.Level
		pData = next(po for po in battle.AllPkmnData if po.Id == p.Pokemon_Id)
		hp = statservice.GenerateStat(p, pData, StatEnum.HP)
		newValue += hp
		newValue += statservice.GenerateStat(p, pData, StatEnum.Attack)
		newValue += statservice.GenerateStat(p, pData, StatEnum.Defense)
		newValue += statservice.GenerateStat(p, pData, StatEnum.SpecialAttack)
		newValue += statservice.GenerateStat(p, pData, StatEnum.SpecialDefense)
		newValue += statservice.GenerateStat(p, pData, StatEnum.Speed)
		newValue += (7.5 if p.CurrentAilment in [4,5] and p.Id == battle.TeamBPkmn.Id else 5 if p.CurrentAilment in [4,5] else 2.5 if p.CurrentAilment else 0)
		newValue += (20 if p.CurrentHP < hp/4 else 15 if p.CurrentHP < hp/3 else 10 if p.CurrentHP < hp else 0)

		if newValue > selectedValue:
			selectedPokemon = p
			selectedValue = newValue
	return selectedPokemon

def ChooseAttack(battle: CpuBattle):
	availableMoves = [m for m in battle.TeamBPkmn.LearnedMoves if m.PP > 0]
	if not availableMoves:
		return moveservice.GetMoveById(165) #struggle
	
	if battle.IsWild:
		return choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in availableMoves])
	
	#Choose a KO move
	koAttacks: list[Move] = []
	for m in availableMoves:
		mData = next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId)
		if mData.Power:
			simAttack = battleservice.AttackDamage(mData, battle.TeamBPkmn, battle.TeamAPkmn, battle)
			if simAttack > battle.TeamAPkmn.CurrentHP:
				koAttacks.append(m)
	if koAttacks:
		koAttacks.sort(key=lambda x: (next(mo for mo in battle.AllMoveData if mo.Id == x.MoveId).Power,next(mo for mo in battle.AllMoveData if mo.Id == x.MoveId).Accuracy))
		return next(mo for mo in battle.AllMoveData if mo.Id == koAttacks[0].MoveId)

	#if the opponent does not have an ailment and one of the moves gives it
	ailmentMoves = [m for m in battle.TeamBPkmn.LearnedMoves if next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Ailment and m.PP > 0]
	if not battle.TeamAPkmn.CurrentAilment and ailmentMoves:
		return choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in ailmentMoves])
	
	#if the opponent does not have any status effect OR it's not maxed and no damage has been taken
	statDebuffs, statBuffs = MovesWithStatChange(availableMoves, battle.AllMoveData)
	if battle.TeamBPkmn.CurrentHP < statservice.GenerateStat(battle.TeamBPkmn, next(po for po in battle.AllPkmnData if po.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.HP):
		if battle.TeamBPkmn.Nature in [n for n in statservice.GetAllNatures() if n.StatBoost == 2 or n.StatBoost == 4]:
			if statBuffs and not [s for s in battle.TeamAStats if battle.TeamBStats[s] > 0]:
				return choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in statBuffs])
		if statDebuffs and not [s for s in battle.TeamAStats if battle.TeamBStats[s] > 0]:
			return choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in statDebuffs])
	
	#random attack
	attackMoves = [m for m in availableMoves if next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Power > 0]
	return choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in attackMoves]) if attackMoves else choice([next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId) for m in availableMoves])

def MovesWithStatChange(moveList: list[Move], moveData: list[MoveData]):
	debuffMoves: list[Move] = []
	buffMoves: list[Move] = []
	for m in moveList:
		data = next(mo for mo in moveData if mo.Id == m.MoveId)
		if data.StatChanges:
			if [s for s in data.StatChanges if data.StatChanges[s] < 0]:
				debuffMoves.append(m)
			if [s for s in data.StatChanges if data.StatChanges[s] > 0]:
				buffMoves.append(m)
	return debuffMoves, buffMoves
