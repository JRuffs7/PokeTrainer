from enum import Enum


class EventType(Enum):
	SpecialSpawn = 0
	SpecialBattle = 1

class SpecialSpawn(Enum):
	Legendary = 'IsLegendary'
	Fossil = 'IsFossil'
	Starter = 'IsStarter'
	Paradox = 'IsParadox'
	UltraBeast = 'IsUltraBeast'