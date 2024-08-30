import discord

from models.Item import Item
from models.Pokemon import Move, Pokemon, PokemonData
from services import moveservice, pokemonservice


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

class PokemonSelector(discord.ui.Select):
	def __init__(self, team: list[Pokemon], data: list[PokemonData]):
			options=[discord.SelectOption(
						label=f'{pokemonservice.GetPokemonDisplayName(t, next(p for p in data if p.Id == t.Pokemon_Id))}',
            description= f'{pokemonservice.GetBattlePokemonDescription(t, next(p for p in data if p.Id == t.Pokemon_Id))}',
						value=t.Id
					) for t in team]
			super().__init__(options=options, max_values=1, min_values=1, placeholder='Change Pokemon')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.PokemonSelection(inter, self.values[0])

class ItemSelector(discord.ui.Select):
	def __init__(self, items: list[Item]):
			options=[discord.SelectOption(
						label=i.Name,
            description= i.Description,
						value=str(i.Id)
					) for i in items]
			super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Item')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.ItemSelection(inter, self.values[0])