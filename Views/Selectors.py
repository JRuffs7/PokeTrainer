import discord

from middleware.decorators import defer
from models.Pokemon import Pokemon
from services import pokemonservice


class TeamSelector(discord.ui.Select):
	def __init__(self, team: list[Pokemon], defaultId: str = None):
		pkmnData = pokemonservice.GetPokemonByIdList([t.Pokemon_Id for t in team])
		options=[discord.SelectOption(
				label=pokemonservice.GetPokemonDisplayName(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id)),
				description= pokemonservice.GetOwnedPokemonDescription(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id)),
				value=t.Id,
				default=(defaultId and t.Id == defaultId)
		) for t in team]
		super().__init__(options=options, placeholder='Select Pokemon')
	
	@defer
	async def callback(self, inter: discord.Interaction):
			await self.view.PokemonSelection(inter, self.values[0])

class EvolveSelector(discord.ui.Select):
	def __init__(self, data: list):
		if len(data) > 25:
				data = data[:25]
		options=[discord.SelectOption(
				label=f"{d['Pokemon'].Name}",
				description= f"{d['Description']}",
				value=f"{d['Pokemon'].Id}"
				) for d in data
		]
		super().__init__(options=options, placeholder='Evolve Into...')
	
	@defer
	async def callback(self, inter: discord.Interaction):
		await self.view.EvolveSelection(inter, self.values[0])