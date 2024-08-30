from dataaccess import moveda
from models.Move import MoveData
from models.Pokemon import Pokemon, PokemonData


def GetMovesById(ids: list[int]):
	return moveda.GetMovesByProperty(ids, 'Id')

def GetMoveById(id: int):
	return next(m for m in moveda.GetAllMoves() if m.Id == id)

def GenerateMoves(pokemon: Pokemon, data: PokemonData):
	if pokemon.LearnedMoves:
		return
	moves = []
	for move in dict(reversed(sorted(data.LevelUpMoves.items(), key=lambda move: move[1]))):
		if data.LevelUpMoves[move] <= pokemon.Level:
			moves.append(int(move))
		if len(moves) == 4:
			break
	pokemon.LearnedMoves = [MoveData({'MoveId': m.Id, 'PP': m.BasePP}) for m in GetMovesById(moves)]

#def UniqueDamageMoves(moveId: int):
	