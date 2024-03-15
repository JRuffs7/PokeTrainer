import discord
from commands.views.Selection.selectors.HatchSelector import HatchSelector
from middleware.decorators import button_check

from models.Egg import TrainerEgg
from services import itemservice, trainerservice, pokemonservice
from models.Trainer import Trainer


class HatchView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, hatchable: list[TrainerEgg]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		super().__init__(timeout=300)
		self.hatchlist = HatchSelector(hatchable)
		self.add_item(self.hatchlist)

	@button_check
	async def EggSelection(self, inter: discord.Interaction, choices: list[str]):
		self.hatchchoices = choices
		await inter.response.defer()

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='Canceled hatching.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.hatchchoices:
			hatchResults: dict[int,str] = {}
			for i in self.hatchchoices:
				trnEgg = next(e for e in self.trainer.Eggs if e.Id == i)
				hatchResults[trainerservice.TryHatchEgg(self.trainer, trnEgg.Id)] = trnEgg.EggId
			self.clear_items()
			hatchMessage = '\n'.join([f'{itemservice.GetEgg(hatchResults[hr]).Name} hatched into a **{pokemonservice.GetPokemonDisplayName(next(p for p in self.trainer.OwnedPokemon if p.Id == hr))}** +$50' for hr in hatchResults])
			await self.message.edit(content=hatchMessage, view=self)
		await inter.response.defer()


	async def send(self):
		await self.interaction.response.send_message(view=self)
		self.message = await self.interaction.original_response()
