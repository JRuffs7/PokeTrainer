from dataaccess import moveda
from models.Move import MoveData
from models.Pokemon import Move, Pokemon, PokemonData
from services import statservice

def GetAllMoves():
	return moveda.GetAllMoves()

def GetTMMoves():
	return moveda.GetTMMoves()

def GetMoveById(id: int):
	return next(m for m in moveda.GetAllMoves() if m.Id == id)

def GetMovesById(ids: list[int]):
	return moveda.GetMovesByProperty(ids, 'Id')

def GenerateMoves(pokemon: Pokemon, data: PokemonData):
	if pokemon.LearnedMoves:
		return
	moves = []
	for move in dict(reversed(sorted(data.LevelUpMoves.items(), key=lambda move: move[1]))):
		if data.LevelUpMoves[move] <= pokemon.Level:
			moves.append(int(move))
		if len(moves) == 4:
			break
	pokemon.LearnedMoves = [Move({'MoveId': m.Id, 'PP': m.BasePP, 'MaxPP': m.BasePP}) for m in GetMovesById(moves)]

def GetEffectiveString(moveType: int, defTypes: list[int], damage: int):
	typeEff = statservice.TypeDamage(moveType, defTypes)
	if typeEff == 0:
		return f'**{damage}** damage. It had no effect!'
	elif typeEff < 1:
		return f'**{damage}** damage. It was not very effective.'
	if typeEff > 1:
		return f'**{damage}** damage. It was super effective!'
	return f'**{damage}** damage.'