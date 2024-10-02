import discord

from Views.Selectors import AmountSelector, TeamSelector, ItemSelector
from middleware.decorators import defer
from models.Trainer import Trainer
from services import commandlockservice, itemservice, pokemonservice, trainerservice

class GiveCandyView(discord.ui.View):

	def __init__(self, trainer: Trainer):
		self.trainer = trainer
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.pkmnchoice = None
		self.itemchoice = None
		self.amountchoice = None
		super().__init__(timeout=300)
		self.AddSelectors()

	def AddSelectors(self):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)
		self.add_item(ItemSelector(self.trainer.Items, itemservice.GetTrainerCandy(self.trainer)))
		self.add_item(TeamSelector([p for p in self.trainerteam if p.Level < 100], descType=1))
		self.add_item(AmountSelector())

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete(delay=0.1)
		return await super().on_timeout()
	
	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		self.pkmnchoice = next(t for t in self.trainerteam if t.Id == choice)
		self.pkmnchoicedata = pokemonservice.GetPokemonById(self.pkmnchoice.Pokemon_Id)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		self.itemchoice = itemservice.GetCandy(int(choice))

	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		self.amountchoice = int(choice)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def exit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await self.on_timeout()

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if self.pkmnchoice and self.itemchoice and self.amountchoice:
			numCandyUsed = pokemonservice.TryUseCandy(self.pkmnchoice, self.pkmnchoicedata, self.itemchoice, min(self.amountchoice,self.trainer.Items[str(self.itemchoice.Id)]))
			if numCandyUsed:
				trainerservice.ModifyItemList(self.trainer, str(self.itemchoice.Id), (0-numCandyUsed))
				trainerservice.UpsertTrainer(self.trainer)
				if self.itemchoice.Experience:
					message = f"{pokemonservice.GetPokemonDisplayName(self.pkmnchoice, self.pkmnchoicedata)} gained {self.itemchoice.Experience*numCandyUsed} XP and is now **Level {self.pkmnchoice.Level}**."
				else:
					message = f"{pokemonservice.GetPokemonDisplayName(self.pkmnchoice, self.pkmnchoicedata)} gained {numCandyUsed} level(s) and is now **Level {self.pkmnchoice.Level}**."
			else:
				message = f'Cannot use **{self.itemchoice.Name}** on {pokemonservice.GetPokemonDisplayName(self.pkmnchoice, self.pkmnchoicedata)}.'
			if not itemservice.GetTrainerCandy(self.trainer) or not [p for p in self.trainerteam if p.Level < 100]:
				commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
				self.clear_items()
				await self.message.edit(content=message, view=self)
				return self.stop()
			self.AddSelectors()
			await self.message.edit(content=message, view=self)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
