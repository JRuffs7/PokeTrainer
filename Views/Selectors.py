import discord

from middleware.decorators import defer
from models.Item import Item
from models.Pokemon import Pokemon
from services import pokemonservice

class PokemonSelector(discord.ui.Select):
	def __init__(self, owned: list[Pokemon], defaultId: str = None, descType: int = 0, customId: str = None):
		pkmnData = pokemonservice.GetPokemonByIdList([t.Pokemon_Id for t in owned])
		options=[discord.SelectOption(
			label=pokemonservice.GetPokemonDisplayName(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id)),
			description= pokemonservice.GetOwnedPokemonDescription(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id), descType),
			value=t.Id,
			default=(defaultId and t.Id == defaultId)
		) for t in owned]
		super().__init__(options=options, placeholder='Select Pokemon', custom_id=(customId or discord.utils.MISSING))
	
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
		) for d in data]
		super().__init__(options=options, placeholder='Evolve Into...')
	
	@defer
	async def callback(self, inter: discord.Interaction):
		await self.view.EvolveSelection(inter, self.values[0])

class ItemSelector(discord.ui.Select):
	def __init__(self, trainerItems: dict[str,int], items: list[Item]):
		options=[discord.SelectOption(
			label=f'{i.Name} ({trainerItems[str(i.Id)]} left)',
			description= i.Description,
			value=str(i.Id)
		) for i in items]
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Item')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.ItemSelection(inter, self.values[0])

class AmountSelector(discord.ui.Select):
	def __init__(self):
		options=[discord.SelectOption(
			label=f'{n}',
			value=f'{n}'
		) for n in range(1,26)]
		super().__init__(options=options, placeholder='Select Amount')
	
	@defer
	async def callback(self, inter: discord.Interaction):
		await self.view.AmountSelection(inter, self.values[0])