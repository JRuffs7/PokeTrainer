class Base:
  Id: int
  Name: str
  Url: str

  def __init__(self, dict):
    vars(self).update(dict)