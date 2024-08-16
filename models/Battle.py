from models.Pokemon import Pokemon, PokemonData


class Battle:
	TeamAPokemon: Pokemon|None = None
	TeamBPokemon: Pokemon|None = None
	TeamAData: PokemonData|None = None
	TeamBData: PokemonData|None = None
	LastTeamAMove: int|None = None
	LastTeamBMove: int|None = None
	TeamAAccuracy: int = 100
	TeamBAccuracy: int = 100
	TeamAEvasion: int = 100
	TeamBEvasion: int = 100
	TeamAPhysReduce: bool = False
	TeamBPhysReduce: bool = False
	TeamASpReduce: bool = False
	TeamBSpReduce: bool = False
