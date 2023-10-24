from typing import List, Dict

class Type:
  Type: str
  Weakness: List[str]
  Resistant: List[str]
  Immune: List[str]

  def __init__(self, dict: Dict | None):
    self.Type = dict.get('Type') or '' if dict else ''
    weak = dict.get('Weakness') if dict else []
    self.Weakness = weak or [] if isinstance(
        weak, List) else weak.value if weak else []
    res = dict.get('Resistance') if dict else []
    self.Resistant = res or [] if isinstance(
        res, List) else res.value if res else []
    immune = dict.get('Immune') if dict else []
    self.Immune = immune or [] if isinstance(
        immune, List) else immune.value if immune else []