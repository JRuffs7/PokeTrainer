import discord
from globals import TrainerColor
from middleware.decorators import defer

from services import commandlockservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class DeleteView(discord.ui.View):
  
	def __init__(self, trainer: Trainer):
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
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		commandlockservice.DeleteEliteFourLock(self.trainer.ServerId, self.trainer.UserId)
		trainerservice.DeleteTrainer(self.trainer)
		await self.message.edit(embed=discordservice.CreateEmbed(
			'Deleted Trainer', 
			'We are sorry to see you go.\nFeel free to start your journey again using the **/starter** command!',
			TrainerColor), view=None)
		self.stop()

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(embed=discordservice.CreateEmbed(
			'Delete Trainer?', 
			'Are you sure you wish to delete all your trainer data?',
			TrainerColor), view=self)
		self.message = await inter.original_response()
