from dataclasses import dataclass, field, fields
import enum
from models.Move import MoveData
from models.Pokemon import Pokemon, PokemonData

class BattleAction(enum.Enum):
	Attack = 0
	Charge = 1
	Swap = 2
	Item = 3
	Pokeball = 4
	Flee = 5

@dataclass
class BattleTurn:
	TurnNum: int = 0
	TeamA: bool = False
	Action: BattleAction|None = None
	Move: MoveData|None = None
	DamageDone: int|None = None

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj

@dataclass
class CpuBattle:
	IsWild: bool = True
	TeamAPkmn: Pokemon | None = None
	TeamBPkmn: Pokemon | None = None
	AllPkmnData: list[PokemonData] = field(default_factory=list)
	AllMoveData: list[MoveData] = field(default_factory=list)
	Turns: list[BattleTurn] = field(default_factory=list)
	TeamAStats: dict = field(default_factory=dict)
	TeamBStats: dict = field(default_factory=dict)
	TeamAImmune: bool = False
	TeamBImmune: bool = False
	TeamABind: int = 0
	TeamBBind: int = 0
	TeamAPhysReduce: int = 0
	TeamBPhysReduce: int = 0
	TeamASpecReduce: int = 0
	TeamBSpecReduce: int = 0

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj

	@classmethod
	def reset_stats(cls, teamA: bool):
		if teamA:
			cls.TeamAStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
		else:
			cls.TeamBStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}