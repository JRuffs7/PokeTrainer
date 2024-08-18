import discord
from middleware.decorators import defer

from services import commandlockservice, trainerservice
from models.Trainer import Trainer


class DeleteView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		super().__init__(timeout=30)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.green)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await self.on_timeout()

	@discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		trainerservice.DeleteTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content=f"We are sorry to see you go.\nFeel free to start your journey again using the **/starter** command!", embed=None, view=None)

	async def send(self):
		await self.interaction.followup.send(content=f"Are you sure you wish to delete all your trainer data?", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
