from dataclasses import dataclass, field, fields
import enum
from models.Move import MoveData
from models.Pokemon import Pokemon, PokemonData
from models.Item import Item

class BattleAction(enum.Enum):
	Error = -1
	Attack = 0
	Missed = 1
	Failed = 2
	Charge = 3
	Recharge = 4
	Sleep = 5
	Frozen = 6
	Paralyzed = 7
	Confused = 8
	Swap = 9
	Item = 10
	Pokeball = 11
	Flee = 12
	Defeated = 13

@dataclass
class BattleTurn:
	TurnNum: int = 0
	TeamA: bool = False
	PokemonId: str|None = None
	Action: BattleAction|None = None
	Move: MoveData|None = None
	DamageDone: int|None = None
	ItemUsed: Item|None = None
	ItemUsedOnId: str|None = None

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj

@dataclass
class CpuBattle:
	CurrentTurn: int = 1
	IsWild: bool = True
	TeamAPkmn: Pokemon | None = None
	TeamBPkmn: Pokemon | None = None
	AllPkmnData: list[PokemonData] = field(default_factory=list)
	AllMoveData: list[MoveData] = field(default_factory=list)
	Turns: list[BattleTurn] = field(default_factory=list)
	TeamAStats: dict[str,int] = field(default_factory=dict)
	TeamBStats: dict[str,int] = field(default_factory=dict)
	TeamATrapId: int | None = None
	TeamBTrapId: int | None = None
	TeamAConsAttacks: int = 0
	TeamBConsAttacks: int = 0
	TeamAConfusion: int = 0
	TeamBConfusion: int = 0
	TeamATrap: int = 0
	TeamBTrap: int = 0
	TeamBConfusion: int = 0
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