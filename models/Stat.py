from models.Base import Base

class Stat(Base):

  def __init__(self, dict):
    super(Stat, self).__init__(dict)

class Nature(Base):
  StatBoost: int
  StatDecrease: int

  def __init__(self, dict):
    super(Nature, self).__init__(dict)
    
class Type(Base):
  Weakness: list[int]
  Resistant: list[int]
  Immune: list[int]

  def __init__(self, dict):
    super(Type, self).__init__(dict)