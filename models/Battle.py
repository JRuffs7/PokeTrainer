from dataclasses import dataclass, field, fields
import enum
from models.Move import MoveData
from models.Pokemon import Pokemon, PokemonData

class BattleAction(enum.Enum):
	Attack: 0
	Swap: 1
	Item: 2
	Flee: 3

@dataclass
class CpuBattle:
	IsWild: bool = True
	TeamAPkmn: Pokemon | None = None
	TeamBPkmn: Pokemon | None = None
	AllPkmnData: list[PokemonData] = field(default_factory=list)
	AllMoveData: list[MoveData] = field(default_factory=list)
	TeamAFirst: bool = False
	LastTeamAAction: int|None = None
	LastTeamBAction: int|None = None
	LastTeamAMove: int|None = None
	LastTeamBMove: int|None = None
	TeamAAccuracy: int = 100
	TeamBAccuracy: int = 100
	TeamAEvasion: int = 100
	TeamBEvasion: int = 100
	TeamAPhysReduce: bool = False
	TeamBPhysReduce: bool = False
	TeamASpecReduce: bool = False
	TeamBSpecReduce: bool = False

	@classmethod
	def from_dict(cls, dict):
		field_names = {field.name for field in fields(cls)}
		returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
		return returnObj
