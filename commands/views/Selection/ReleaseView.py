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
		self.pokemonchoices = choices
		await inter.response.defer()


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await self.message.delete()
		await inter.response.send_message(content='Canceled release.',ephemeral=True)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoices:
			pokemon = trainerservice.ReleasePokemon(trainerservice.GetTrainer(inter.guild_id, inter.user.id), self.pokemonchoices)
			await self.message.delete()
			await inter.response.send_message(content=f"You have released {len(self.pokemonchoices)} {pokemon}",ephemeral=True)


	async def send(self):
		await self.interaction.response.send_message(content="Choose Pokemon to release", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
