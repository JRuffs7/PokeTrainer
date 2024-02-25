import discord

from typing import List

from services import trainerservice
from models.Pokemon import Pokemon
from commands.views.selectors.OwnedSelector import OwnedSelector


class ReleasePokemonView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, pokeList: List[Pokemon]):
		self.interaction = interaction
		self.pokeList = pokeList
		super().__init__(timeout=300)
		self.add_item(OwnedSelector(pokeList, 25))


	async def PokemonSelection(self, inter: discord.Interaction, choices):
		self.pokemonchoices = choices
		await inter.response.defer()


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await self.message.delete()
		await inter.response.send_message(content='Canceled release.',ephemeral=True)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoices:
			pokemon = trainerservice.ReleasePokemon(trainerservice.GetTrainer(inter.guild_id, inter.user.id), self.pokemonchoices)
			await self.message.delete()
			await inter.response.send_message(content=f"You have released {len(self.pokemonchoices)} {pokemon}",ephemeral=True)


	async def send(self):
		await self.interaction.response.send_message(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
