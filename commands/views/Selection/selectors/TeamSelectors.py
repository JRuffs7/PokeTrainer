import discord

from models.Pokemon import Pokemon
from services import pokemonservice


class TeamChoice(discord.ui.Select):
	def __init__(self, data: list[Pokemon], adding: bool = False):
		options = [discord.SelectOption(
			label='Add To End Slot',
			description=f'Add selected Pokemon to the end slot on the team.',
			value=f'{len(data)}'
		)] if adding else []
		
		options += [discord.SelectOption(
			label=f'Slot {i+1}: {pokemonservice.GetPokemonDisplayName(data[i])}',
			description=f'{pokemonservice.GetOwnedPokemonDescription(data[i])}',
			value=f'{i}'
			) for i in range(len(data))
		]

		options += [discord.SelectOption(
			label=f'Remove From Team',
			description=f'Remove selected Pokemon from the team.',
			value=f'-1'
		)] if not adding else []
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Select Team Slot')

	async def callback(self, inter: discord.Interaction):
		await self.view.TeamSlotSelection(inter, self.values[0])