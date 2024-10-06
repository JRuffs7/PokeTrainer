import discord

from typing import List
from Views.Selectors import PokemonSelector
from globals import SuccessColor
from middleware.decorators import defer

from models.Trainer import Trainer
from services import commandlockservice, pokemonservice, trainerservice
from models.Pokemon import Pokemon
from services.utility import discordservice


class ReleaseView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemonId: int):
		self.trainer = trainer
		self.data = pokemonservice.GetPokemonById(pokemonId)
		super().__init__(timeout=300)
		self.add_item(PokemonSelector([p for p in trainer.OwnedPokemon if p.Pokemon_Id == pokemonId and p.Id not in trainer.Team and p.Id not in trainer.Daycare], max=True))

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		self.pokemonchoices = choices

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await self.on_timeout()

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if self.pokemonchoices:
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			await self.message.delete(delay=0.1)
			trainerservice.ReleasePokemon(self.trainer, self.pokemonchoices)
			trainerservice.UpsertTrainer(self.trainer)
			await inter.followup.send(embed=discordservice.CreateEmbed(
				'Released', 
				f'<@{self.trainer.UserId}> has released **{len(self.pokemonchoices)} {self.data.Name}**',
				SuccessColor,
				thumbnail=inter.user.display_avatar.url))

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
