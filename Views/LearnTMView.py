import discord
from Views.Selectors import MoveSelector, PokemonSelector
from globals import SuccessColor
from middleware.decorators import defer

from models.Pokemon import Pokemon, PokemonData
from services import commandlockservice, moveservice, pokemonservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class LearnTMView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemon: list[Pokemon], data: list[PokemonData], tm: int):
		self.trainer = trainer
		self.tm = moveservice.GetMoveById(tm)
		self.pokemonchoice = None
		self.replacing = None
		super().__init__(timeout=300)
		self.add_item(PokemonSelector(pokemon))
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

	async def PokemonSelection(self, inter: discord.Interaction, choice: str): 
		self.pokemonchoice = next(p for p in self.trainer.OwnedPokemon if p.Id == choice)
		self.choicedata = pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon_Id)

	async def MoveSelection(self, inter: discord.Interaction, choice: str): 
		self.replacing = moveservice.GetMoveById(int(choice))

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()

	async def next_button(self, inter: discord.Interaction):
		if not self.pokemonchoice:
			return await inter.response.defer()
		if len(self.pokemonchoice.LearnedMoves) < 4:
			await inter.response.defer(thinking=True)
			return await self.LearnTM(inter)

		await inter.response.defer()
		self.clear_items()
		self.add_item(MoveSelector([m for m in self.pokemonchoice.LearnedMoves]))
		cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.gray)
		cnclbtn.callback = self.cancel_button
		self.add_item(cnclbtn)
		sbmtbtn = discord.ui.Button(label="Submit", style=discord.ButtonStyle.green)
		sbmtbtn.callback = self.submit_button
		self.add_item(sbmtbtn)
		await self.message.edit(content='Please select a move to replace.', view=self)

	async def submit_button(self, inter: discord.Interaction):
		await inter.response.defer(thinking=True)
		await self.LearnTM(inter)

	async def LearnTM(self, inter: discord.Interaction):
		if not pokemonservice.LearnNewMove(self.pokemonchoice, self.tm, self.replacing):
			return await self.message.edit(content='Please select a move to replace.')

		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		trainerservice.ModifyTMList(self.trainer, str(self.tm.Id), -1)
		trainerservice.UpsertTrainer(self.trainer)
		embed = discordservice.CreateEmbed(
			f"TM Used",
			f'<@{self.trainer.UserId}> used **TM{self.tm.Id}-{self.tm.Name}** on **{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, self.choicedata)}**!{f" It forgot the move **{self.replacing.Name}**." if self.replacing else ""}',
			SuccessColor)
		await inter.followup.send(embed=embed)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(content='Please select a Pokemon to use the TM on.', view=self)
		self.message = await inter.original_response()
