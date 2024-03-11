from random import choice

from models.enums import PokemonCount, StatCompare


def GetRandomStatCompare():
	return choice(list(StatCompare))

def GetRandomCount():
	return choice(list(PokemonCount))