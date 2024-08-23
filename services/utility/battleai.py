from random import choice
from models.Battle import CpuBattle
from models.Pokemon import Pokemon, Move
from models.Stat import StatEnum
from services import battleservice, moveservice, statservice, typeservice


def ShouldSwitchPokemon(battle: CpuBattle, cpuTeam: list[Pokemon]):
	if len(cpuTeam) == 1:
		return None
	
	validSwaps = [p for p in cpuTeam if p.CurrentHP > (statservice.GenerateStat(p, next(po for po in battle.AllPkmnData if po.Id == p.Pokemon_Id), StatEnum.HP)/3) and p.CurrentAilment > 3]
	if not validSwaps:
		return None
	
	tookDamage = battle.TeamBPkmn.CurrentHP < statservice.GenerateStat(battle.TeamBPkmn, next(po for po in battle.AllPkmnData if po.Id == battle.TeamBPkmn.Pokemon_Id), StatEnum.HP)

	#Danger from moves
	levelDiff = battle.TeamBPkmn.Level - battle.TeamAPkmn.Level
	attMoves = [m for m in battle.TeamAPkmn.LearnedMoves if (next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Power or 0) > 70]
	maxEff = [{ 'Data': next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId), 'Effect': typeservice.AttackEffect(m, next(p for p in battle.AllPkmnData if p.Id == battle.TeamBPkmn.Pokemon_Id).Types) } for m in attMoves] if attMoves else []
	superEffectMoves = [m for m in maxEff if m['Effect'] >= 2]
	highPowerSuper = [m for m in superEffectMoves if m['Data'].Power >= 90]
	if tookDamage and -5<levelDiff<5 and superEffectMoves and choice(range(101)) < (50 if highPowerSuper else 25):
		return choice(validSwaps)

	#Danger from status/stats
	if battle.TeamBPkmn.CurrentAilment == 6 or battle.TeamBPkmn.CurrentAilment <= 3 or battle.TeamBAccuracy == -6 or battle.TeamBEvasion == -6:
		return choice(validSwaps)
	return None


def ChooseAttack(battle: CpuBattle):
	availableMoves = [m for m in battle.TeamBPkmn.LearnedMoves if m.PP > 0]
	if not availableMoves:
		return Move({'MoveId': 165, 'PP': 1}) #struggle
	
	if battle.IsWild:
		return choice(availableMoves)
	
	ailmentMoves = [m for m in battle.TeamBPkmn.LearnedMoves if next(mo for mo in battle.AllMoveData if mo.Id == m.MoveId).Ailment and m.PP > 0]
	if not battle.TeamAPkmn.CurrentAilment and ailmentMoves:
		ranks = {}
		for move in ailmentMoves:
