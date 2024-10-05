import discord

from middleware.decorators import defer
from models.Item import Item
from models.Pokemon import Move, Pokemon
from services import moveservice, pokemonservice

class PokemonSelector(discord.ui.Select):
	def __init__(self, owned: list[Pokemon], defaultId: str = None, descType: int = 0, customId: str = None, defer: bool = True):
		self.defer = defer
		if len(owned) > 25:
			owned = owned[0:25]
		pkmnData = pokemonservice.GetPokemonByIdList([t.Pokemon_Id for t in owned])
		options=[discord.SelectOption(
			label=pokemonservice.GetPokemonDisplayName(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id)),
			description= pokemonservice.GetPokemonDescription(t, next(p for p in pkmnData if t.Pokemon_Id == p.Id), descType),
			value=t.Id,
			default=(defaultId and t.Id == defaultId)
		) for t in owned]
		super().__init__(options=options, placeholder='Select Pokemon', custom_id=(customId or discord.utils.MISSING))
	
	async def callback(self, inter: discord.Interaction):
		if self.defer:
			await inter.response.defer()
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
		super().__init__(options=options, placeholder='Select Item')
	
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

class TeamSelector(discord.ui.Select):
	def __init__(self, data: list[Pokemon], adding: bool = False):
		pkmnData = pokemonservice.GetPokemonByIdList([d.Pokemon_Id for d in data])
		options = [discord.SelectOption(
			label='Add To End Slot',
			description=f'Add selected Pokemon to the end slot on the team.',
			value=f'{len(data)}'
		)] if adding and len(data) < 6 else []

		options += [discord.SelectOption(
			label=f'Remove From Team',
			description=f'Remove selected Pokemon from the team.',
			value='-1'
		)] if not adding else []
		
		options += [discord.SelectOption(
			label=f'Slot {i+1}: {pokemonservice.GetPokemonDisplayName(data[i], next(p for p in pkmnData if data[i].Pokemon_Id == p.Id))}',
			description=f'{pokemonservice.GetPokemonDescription(data[i], next(p for p in pkmnData if data[i].Pokemon_Id == p.Id), 3)}',
			value=f'{i}'
			) for i in range(len(data))
		]
		super().__init__(options=options, placeholder='Select Team Slot')

	@defer
	async def callback(self, inter: discord.Interaction):
		await self.view.TeamSelection(inter, self.values[0])

class MoveSelector(discord.ui.Select):
	def __init__(self, pkmnMoves: list[Move]):
			moves = moveservice.GetMovesById([m.MoveId for m in pkmnMoves])
			options=[discord.SelectOption(
						label=f'{m.Name}',
            description= f'PP: {next(move for move in pkmnMoves if move.MoveId == m.Id).PP}/{m.BasePP} | Power: {m.Power or "-"} | Accuracy: {m.Accuracy or "-"} | StatChngs.: {len(m.StatChanges) or "-"}',
						value=f'{m.Id}'
					) for m in moves]
			super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Attack')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.MoveSelection(inter, self.values[0])