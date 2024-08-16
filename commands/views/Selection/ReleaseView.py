import discord

from typing import List
from middleware.decorators import defer

from services import commandlockservice, trainerservice
from models.Pokemon import Pokemon
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector


class ReleaseView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, pokeList: List[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.pokeList = pokeList
		super().__init__(timeout=300)
		self.add_item(OwnedSelector(pokeList))

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		self.pokemonchoices = choices

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content='Canceled release.', embed=None, view=None)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoices:
			pokemon = trainerservice.ReleasePokemon(trainerservice.GetTrainer(inter.guild_id, inter.user.id), self.pokemonchoices)
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			await self.message.edit(content=f"You have released {len(self.pokemonchoices)} {pokemon}", embed=None, view=None)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
