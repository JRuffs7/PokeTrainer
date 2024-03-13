from random import choice

from models.enums import PokemonCount, StatCompare


def GetRandomStatCompare():
	return choice(list(StatCompare))

def GetRandomCount():
	return choice(list(PokemonCount))

def TopThreeWinners(sortedList: dict[str,int|float], smallFirst: bool):
	winners: list[tuple[int,int]] = []
	compareEntry = None
	numWinners = 0
	for k, v in sortedList.items():
		if compareEntry == None:
			winners.append((int(k),4))
			compareEntry = v
			numWinners += 1
		elif v == compareEntry:
			reward = 4 if numWinners == 1 else 3 if numWinners == 2 else 2
			winners.append((int(k),reward))
		elif (v > compareEntry and smallFirst) or (v < compareEntry and not smallFirst):
			if numWinners < 3:
				reward = 3 if numWinners == 1 else 2
				winners.append((int(k),reward))
				compareEntry = v
				numWinners += 1
			else:
				break
	return winners