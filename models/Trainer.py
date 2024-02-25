from models.Pokemon import Pokemon

class Trainer:
  UserId: int
  ServerId: int
  Health: int
  Money: int
  PokeballList: list[int]
  PotionList: list[int]
  OwnedPokemon: list[Pokemon]
  Team: list[str]
  Badges: list[int]

  def __init__(self, dict):
    vars(self).update(dict)
    self.OwnedPokemon = [Pokemon(p) for p in self.OwnedPokemon]
    # self.UserId = dict.get('UserId') or 0 if dict else 0
    # self.ServerId = dict.get('ServerId') or 0 if dict else 0
    # owned = dict.get('OwnedPokemon') if dict else []
    # self.OwnedPokemon = [Pokemon(p) for p in owned] if isinstance(
    #     owned, List) else ([Pokemon(p)
    #                         for p in owned.value] if owned else [])
    # team = dict.get('Team') if dict else []
    # self.Team = team or [None]*6 if isinstance(
    #     team, List) else team.value if team else [None]*6
    # badges = dict.get('Badges') if dict else []
    # self.Badges = badges or [] if isinstance(
    #     badges, List) else badges.value if badges else []
    # self.Health = dict.get('Health') or 0 if dict else 0
    # self.Money = dict.get('Money') or 0 if dict else 0
    # pkbl = dict.get('PokeballList') if dict else []
    # self.PokeballList = [int(p) for p in pkbl] if isinstance(
    #     pkbl, List) else ([int(p) for p in pkbl.value] if pkbl else [])
    # ptn = dict.get('PotionList') if dict else []
    # self.PotionList = [int(p) for p in ptn] if isinstance(
    #     ptn, List) else ([int(p) for p in ptn.value] if ptn else [])
