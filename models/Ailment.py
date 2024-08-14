from models.Base import Base

class Ailment(Base):
  MoveIds: list[int]

  def __init__(self, dict):
    super(Ailment, self).__init__(dict)