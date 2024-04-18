import discord

from typing import List
from middleware.decorators import button_check

from services import trainerservice
from models.Pokemon import Pokemon
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector


class ReleaseView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, pokeList: List[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.pokeList = pokeList
		super().__init__(timeout=300)
		self.add_item(OwnedSelector(pokeList))


	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		await inter.response.defer()
		self.pokemonchoices = choices


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='Canceled release.')

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoices:
			pokemon = trainerservice.ReleasePokemon(trainerservice.GetTrainer(inter.guild_id, inter.user.id), self.pokemonchoices)
			await self.message.delete(delay=0.01)
			await inter.followup.send(content=f"You have released {len(self.pokemonchoices)} {pokemon}",ephemeral=True)


	async def send(self):
		await self.interaction.followup.send(content="Choose Pokemon to release", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
