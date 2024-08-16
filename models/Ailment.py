from models.Base import Base

class Ailment(Base):

  def __init__(self, dict):
    super(Ailment, self).__init__(dict)