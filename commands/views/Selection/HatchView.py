import discord
from commands.views.Selection.selectors.HatchSelector import HatchSelector
from middleware.decorators import defer

from models.Egg import TrainerEgg
from services import commandlockservice, itemservice, trainerservice, pokemonservice
from models.Trainer import Trainer


class HatchView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, hatchable: list[TrainerEgg]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.hatchchoices = None
		super().__init__(timeout=300)
		self.hatchlist = HatchSelector(hatchable)
		self.add_item(self.hatchlist)

	async def on_timeout(self):
		await self.message.delete()
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def EggSelection(self, inter: discord.Interaction, choices: list[str]):
		self.hatchchoices = choices

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content='Canceled hatching.', view=None)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.hatchchoices:
			hatchResults: dict[int,str] = {}
			for i in self.hatchchoices:
				trnEgg = next(e for e in self.trainer.Eggs if e.Id == i)
				hatchResults[trainerservice.TryHatchEgg(self.trainer, trnEgg.Id)] = trnEgg.EggId
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			hatchMessage = '\n'.join([f'{itemservice.GetEgg(hatchResults[hr]).Name} hatched into a **{pokemonservice.GetPokemonDisplayName(next(p for p in self.trainer.OwnedPokemon if p.Id == hr))}** +$50' for hr in hatchResults])
			await self.message.edit(content=hatchMessage, view=None)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
