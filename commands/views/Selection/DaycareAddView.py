from datetime import UTC, datetime
import discord
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import DateFormat
from middleware.decorators import defer

from models.Pokemon import Pokemon
from services import commandlockservice, pokemonservice, trainerservice
from models.Trainer import Trainer


class DaycareAddView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, pokemon: list[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.pokemon = pokemon
		self.pokemonchoices = None if len(pokemon) > 1 else [p.Id for p in pokemon]
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(pokemon, (4 if trainerservice.HasRegionReward(self.trainer, 6) else 2) - len(trainer.Daycare))
		self.add_item(self.ownlist)
		if self.pokemonchoices:
			self.clear_items()

	async def on_timeout(self):
		await self.message.delete()
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		self.pokemonchoices = choices

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction, button: discord.ui.Button):
		self.clear_items()
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content='Did not add to daycare.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if not self.pokemonchoices:
			return
		await self.SubmitPokemon()
		
	async def SubmitPokemon(self):
		self.clear_items()
		pkmnList = [next(p for p in self.trainer.OwnedPokemon if p.Id == c) for c in self.pokemonchoices]
		for p in self.pokemonchoices:
			if len(self.trainer.Daycare) < (4 if trainerservice.HasRegionReward(self.trainer, 6) else 2):
				self.trainer.Daycare[p] = datetime.now(UTC).strftime(DateFormat)
		trainerservice.UpsertTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content=f'Added **{"** and **".join([pokemonservice.GetPokemonDisplayName(p) for p in pkmnList])}** to your daycare.', view=self)

	async def send(self):
		if self.pokemonchoices:
			await self.interaction.followup.send(content='Processing...')
			self.message = await self.interaction.original_response()
			await self.SubmitPokemon()
		else:
			await self.interaction.followup.send(view=self)
			self.message = await self.interaction.original_response()
