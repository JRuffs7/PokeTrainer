import discord
from Views.Selectors import MoveSelector
from globals import SuccessColor
from middleware.decorators import defer

from models.Move import MoveData
from models.Pokemon import Move, Pokemon, PokemonData
from services import commandlockservice, moveservice, pokemonservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class LearnMovesView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemon: Pokemon, data: PokemonData, available: list[MoveData]):
		self.trainer = trainer
		self.pokemon = pokemon
		self.data = data
		self.available = available
		self.newmove = True
		self.learning = None
		self.replacing = None
		super().__init__(timeout=300)
		self.add_item(MoveSelector([Move({'MoveId': m.Id, 'PP': m.BasePP}) for m in available]))
		cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.gray)
		cnclbtn.callback = self.cancel_button
		self.add_item(cnclbtn)
		nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
		nxtbtn.callback = self.next_button
		self.add_item(nxtbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def MoveSelection(self, inter: discord.Interaction, choice: str): 
		if self.newmove:
			self.learning = moveservice.GetMoveById(int(choice))
		else:
			self.replacing = moveservice.GetMoveById(int(choice))

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()

	async def next_button(self, inter: discord.Interaction):
		if len(self.pokemon.LearnedMoves) < 4:
			await inter.response.defer(thinking=True)
			return await self.LearnNewMove(inter)
		await inter.response.defer()

		self.newmove = False
		self.clear_items()
		self.add_item(MoveSelector([m for m in self.pokemon.LearnedMoves]))
		cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.gray)
		cnclbtn.callback = self.cancel_button
		self.add_item(cnclbtn)
		sbmtbtn = discord.ui.Button(label="Submit", style=discord.ButtonStyle.green)
		sbmtbtn.callback = self.submit_button
		self.add_item(sbmtbtn)
		await self.message.edit(content='Please select a move to replace.', view=self)

	async def submit_button(self, inter: discord.Interaction):
		await inter.response.defer(thinking=True)
		await self.LearnNewMove(inter)

	async def LearnNewMove(self, inter: discord.Interaction):
		if self.learning and not pokemonservice.LearnNewMove(self.pokemon, self.learning, self.replacing):
			return await self.message.edit(content='Please select a move to replace.')

		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		self.trainer.Money -= 500
		trainerservice.UpsertTrainer(self.trainer)
		embed = discordservice.CreateEmbed(
			f"New Move Taught",
			f'<@{self.trainer.UserId}> spent **$500** to teach **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)}** the move **{self.learning.Name}**!{f" It forgot the move **{self.replacing.Name}**." if self.replacing else ""}',
			SuccessColor)
		await inter.followup.send(embed=embed)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(content='Please select a move to learn.', view=self)
		self.message = await inter.original_response()
