from models.Base import Base

class Move(Base):
	BasePP: int|None
	Accuracy: int|None
	Power: int|None
	Priority: int
	UniqueDamage: bool
	CritRate: int
	MinAttacks: int
	MaxAttacks: int
	Healing: int
	Ailment: int|None
	AilmentChance: int
	AttackType: str
	MoveType: int
	Targets: int
	StatChanges: dict[str,int]
	StatChance: int|None
	MachineID: str|None
	Cost: int|None

	def __init__(self, dict):
		super(Move, self).__init__(dict)