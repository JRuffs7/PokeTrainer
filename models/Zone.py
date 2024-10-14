from models.Base import Base

class Zone(Base):
	Types: list[int]
	FightOnly: bool

	def __init__(self, dict):
		super(Zone, self).__init__(dict)