from enum import Enum


class EventType(Enum):
	SpecialSpawn = 0
	StatCompare = 1
	PokemonCount = 2

class SpecialSpawn(Enum):
	Legendary = 'IsLegendary'
	Fossil = 'IsFossil'
	Starter = 'IsStarter'
	Paradox = 'IsParadox'
	UltraBeast = 'IsUltraBeast'