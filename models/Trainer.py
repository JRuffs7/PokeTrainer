from typing import Dict, List

from models.Pokemon import PokedexEntry
from services import pokemonservice, gymservice


class Trainer:
  UserId: int
  ServerId: int
  OwnedPokemon: List[PokedexEntry]
  Team: List[str]
  Badges: List[int]
  Health: int
  Money: int
  Fights: int
  TotalCaught: int
  PokeballList: List[int]
  PotionList: List[int]

  def __init__(self, dict: Dict | None):
    self.UserId = dict.get('UserId') or 0 if dict else 0
    self.ServerId = dict.get('ServerId') or 0 if dict else 0
    owned = dict.get('OwnedPokemon') if dict else []
    self.OwnedPokemon = [PokedexEntry(p) for p in owned] if isinstance(
        owned, List) else ([PokedexEntry(p)
                            for p in owned.value] if owned else [])
    team = dict.get('Team') if dict else []
    self.Team = team or [None]*6 if isinstance(
        team, List) else team.value if team else [None]*6
    badges = dict.get('Badges') if dict else []
    self.Badges = badges or [] if isinstance(
        badges, List) else badges.value if badges else []
    self.Health = dict.get('Health') or 0 if dict else 0
    self.Money = dict.get('Money') or 0 if dict else 0
    self.Fights = dict.get('Fights') or 0 if dict else 0
    self.TotalCaught = dict.get('TotalCaught') or 0 if dict else 0
    pkbl = dict.get('PokeballList') if dict else []
    self.PokeballList = [int(p) for p in pkbl] if isinstance(
        pkbl, List) else ([int(p) for p in pkbl.value] if pkbl else [])
    ptn = dict.get('PotionList') if dict else []
    self.PotionList = [int(p) for p in ptn] if isinstance(
        ptn, List) else ([int(p) for p in ptn.value] if ptn else [])

  def __str__(self):
    uniquePkmn = len(set([x.PokedexId for x in self.OwnedPokemon]))
    totalPkmn = pokemonservice.GetPokemonCount()
    totalBadges = len(gymservice.GetAllBadges())

    return f"__Stats__\nHP: {self.Health}\nFights: {self.Fights}\n${self.Money}\n\n__Pokemon__\nPokedex: {uniquePkmn}/{totalPkmn} ({round((uniquePkmn*100)/totalPkmn)}%)\nPokemon Owned: {len(self.OwnedPokemon)}\nShiny Count: {len([x for x in self.OwnedPokemon if x.Pokemon.IsShiny])}\nTotal Caught: {self.TotalCaught}\n\n__Gyms__\nBadges: {len(self.Badges)}/{totalBadges}"

