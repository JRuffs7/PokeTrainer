import discord
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from Views.Selectors import PokemonSelector
from globals import TradeColor, botImage
from middleware.decorators import defer

from models.Trainer import Trainer
from services import commandlockservice, statservice, trainerservice, pokemonservice
from models.Pokemon import Pokemon, PokemonData
from services.utility import discordservice


class TradeView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, targetTrainer: Trainer, userTradeList: list[Pokemon], targetTradeList: list[Pokemon], userData: PokemonData, targetData: PokemonData):
		self.trainer = trainer
		self.targettrainer = targetTrainer
		self.usertradelist = userTradeList
		self.targettradelist = targetTradeList
		self.userdata = userData
		self.targetdata = targetData
		self.initial = True
		self.message = None
		self.trademessage = None
		super().__init__(timeout=300)
		cnclBtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
		cnclBtn.callback = self.cancel_button
		sndbtn = discord.ui.Button(label="Send", style=discord.ButtonStyle.success)
		sndbtn.callback = self.submit_button
		self.add_item(cnclBtn)
		self.add_item(sndbtn)
		self.ownlist = PokemonSelector(self.usertradelist, customId='ownedTradeList')
		self.targetlist = PokemonSelector(self.targettradelist, customId='targetTradeList')
		self.add_item(self.ownlist)
		self.add_item(self.targetlist)

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		if self.message:
			await self.message.delete(delay=0.1)
		if self.trademessage:
			await self.trademessage.delete(delay=0.1)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		if inter.data['custom_id'] == 'ownedTradeList':
			self.userpkmnchoice = next(p for p in self.usertradelist if p.Id == choice)
		else:
			self.targetpkmnchoice = next(p for p in self.targettradelist if p.Id == choice)

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		self.stop()
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		if inter.user.id == self.targettrainer.UserId:
			await self.trademessage.edit(content=f'<@{self.trainer.UserId}>\nTrade offer was rejected.', embed=None, view=None)
		elif self.trademessage:
			await self.trademessage.edit(content='Trade was canceled.', embed=None, view=None)
		else:
			await self.message.edit(content='Trade was canceled.', embed=None, view=None)


	async def submit_button(self, inter: discord.Interaction):
		if not self.userpkmnchoice or not self.targetpkmnchoice:
			return await inter.response.defer()
		await inter.response.defer(thinking=(self.trademessage is None))

		if self.initial:
			self.clear_items()
			await self.message.delete(delay=0.01)
			rjctbtn = discord.ui.Button(label="Reject", style=discord.ButtonStyle.danger)
			rjctbtn.callback = self.cancel_button
			acptbtn = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
			acptbtn.callback = self.submit_button
			self.add_item(rjctbtn)
			self.add_item(acptbtn)
			self.initial = False

			embed = discordservice.CreateEmbed(
				f'Trade Offer From {inter.user.display_name}', 
				f'__You Give__:\n{self.PrintPkmnDetails(self.targetpkmnchoice, self.targetdata)}\n\n__You Receive__:\n{self.PrintPkmnDetails(self.userpkmnchoice, self.userdata)}', 
				TradeColor,
				thumbnail=botImage)
			await inter.followup.send(content=f'<@{self.targettrainer.UserId}>', embed=embed, view=self)
			self.trademessage = await inter.original_response()
		else:
			if inter.user.id != self.targettrainer.UserId:
				return
			if commandlockservice.IsEliteFourLocked(self.targettrainer.ServerId, self.targettrainer.UserId):
				commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
				self.stop()
				return await self.trademessage.edit(content=f'One user is currently taking on the Elite Four! Try again later.', embed=None, view=None)
			if commandlockservice.IsLocked(self.targettrainer.ServerId, self.targettrainer.UserId):
				return await self.trademessage.edit(content=f'One user is currently in an interaction! Finish the previous command and try again.')
			self.targettrainer = trainerservice.GetTrainer(self.targettrainer.ServerId, self.targettrainer.UserId)
			self.targetpkmnchoice = next((p for p in self.targettrainer.OwnedPokemon if p.Id == self.targetpkmnchoice.Id and p.Pokemon_Id == self.targetpkmnchoice.Pokemon_Id), None)
			if not self.targetpkmnchoice:
				return await self.trademessage.edit(content=f'The Pokemon being traded no longer exists. Please try again.', embed=None, view=None)
			trainerservice.TradePokemon(self.trainer, self.userpkmnchoice, self.targettrainer, self.targetpkmnchoice)
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			self.stop()
			return await self.trademessage.edit(content=f'<@{self.trainer.UserId}> traded away **{pokemonservice.GetPokemonDisplayName(self.userpkmnchoice, self.userdata)}** to <@{self.targettrainer.UserId}> for **{pokemonservice.GetPokemonDisplayName(self.targetpkmnchoice, self.targetdata)}**', embed=None, view=None)

	def PrintPkmnDetails(self, pokemon: Pokemon, data: PokemonData):
		pkmnData = t2a(
			body=[
				['Level:', pokemon.Level], 
				['Height:', pokemon.Height],
				['Weight:', pokemon.Weight],
				['Color:',f"{data.Color}"],  
				['Types:', f"{'/'.join([statservice.GetType(t).Name for t in data.Types])}"]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"**{pokemonservice.GetPokemonDisplayName(pokemon, data)} ({data.Name})**\n```{pkmnData}```"

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
