class Type:
  Name: str
  Weakness: list[str]
  Resistant: list[str]
  Immune: list[str]

  def __init__(self, dict):
    vars(self).update(dict)