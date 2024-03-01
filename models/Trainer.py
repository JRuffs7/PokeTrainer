from models.Pokemon import Pokemon

class Trainer:
  UserId: int
  ServerId: int
  Health: int
  Money: int
  Pokeballs: dict[str, int]
  Potions: dict[str, int]
  OwnedPokemon: list[Pokemon]
  Team: list[str]
  Badges: list[int]
  LastSpawnTime: str | None

  def __init__(self, dict):
    vars(self).update(dict)
    self.OwnedPokemon = [Pokemon(p) for p in self.OwnedPokemon]
