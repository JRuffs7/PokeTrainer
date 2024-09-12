from models.Base import Base

class MoveData(Base):
	BasePP: int|None
	Accuracy: int|None
	Power: int|None
	Priority: int
	UniqueDamage: bool
	UserDamage: bool
	Recharge: bool
	Charge: bool
	ChargeImmune: bool
	ConsecutiveAttack: bool
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
	StatEffectOpponent: bool
	MachineID: str|None
	Cost: int|None

	def __init__(self, dict):
		super(MoveData, self).__init__(dict)