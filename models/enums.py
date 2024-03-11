from enum import Enum


class EventType(Enum):
	SpecialSpawn = 0
	StatCompare = 1
	PokemonCount = 2

class StatCompare(Enum):
	Lightest = 0
	Shortest = 1
	Heaviest = 2
	Tallest = 3

class PokemonCount(Enum):
	Grass = 0
	Water = 1
	Fire = 2
	Electric = 3
	Ground = 4
	Flying = 5
	Rock = 6
	Ice = 7
	Bug = 8
	Fairy = 9
	Fighting = 10
	Ghost = 11
	Psychic = 12
	Dark = 13
	Steel = 14
	Dragon = 15
	Normal = 16
	Poison = 17
	Male = 18
	Female = 19
	Shiny = 20
	Legendary = 21

class SpecialSpawn(Enum):
	Legendary = 'IsLegendary'
	Fossil = 'IsFossil'
	Starter = 'IsStarter'
	Paradox = 'IsParadox'
	UltraBeast = 'IsUltraBeast'