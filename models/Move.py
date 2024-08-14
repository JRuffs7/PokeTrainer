from models.Base import Base

class Move(Base):
	Accuracy: int|None
	Power: int|None
	UniqueDamage: bool
	MultiAttack: bool
	AttackType: str
	MoveType: int
	Targets: int
	StatChanges: dict[str,int]
	CauseAilment: bool
	EffectChance: int|None
	MachineID: str|None
	Cost: int|None

	def __init__(self, dict):
		super(Move, self).__init__(dict)