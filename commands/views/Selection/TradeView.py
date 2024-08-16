import discord
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from globals import TradeColor
from middleware.decorators import defer

from models.Trainer import Trainer
from services import commandlockservice, trainerservice, pokemonservice
from models.Pokemon import Pokemon, PokemonData
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from services.utility import discordservice


class TradeView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, targetTrainer: Trainer, userTradeList: list[Pokemon], targetTradeList: list[Pokemon], userData: PokemonData, targetData: PokemonData, botimg: str):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.targettrainer = targetTrainer
		self.usertradelist = userTradeList
		self.targettradelist = targetTradeList
		self.userdata = userData
		self.targetdata = targetData
		self.botimg = botimg
		self.initial = True
		super().__init__(timeout=30)
		self.ownlist = OwnedSelector(self.usertradelist, 1, customId='ownedTradeList')
		self.targetlist = OwnedSelector(self.targettradelist, 1, customId='targetTradeList')
		self.add_item(self.ownlist)
		self.add_item(self.targetlist)

	async def on_timeout(self):
		await self.message.delete()
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		if inter.data['custom_id'] == 'ownedTradeList':
			self.userpkmnchoice = next(p for p in self.usertradelist if p.Id == choice[0])
		else:
			self.targetpkmnchoice = next(p for p in self.targettradelist if p.Id == choice[0])

	@discord.ui.button(label='Reject', style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if inter.user.id == self.targettrainer.UserId:
			await self.message.edit(content=f'<@{self.user.id}>\nTrade offer was rejected.', embed=None, view=None)
		else:
			await self.message.edit(content='Trade was canceled.', embed=None, view=None)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)


	@discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if self.initial:
			if not self.userpkmnchoice or not self.targetpkmnchoice or inter.user.id != self.trainer.UserId:
				return
		
			await self.message.delete(delay=0.01)
			self.remove_item(self.ownlist)
			self.remove_item(self.targetlist)
			self.initial = False

			embed = discordservice.CreateEmbed(
				f'Trade Offer From {self.user.display_name}', 
				f'__You Give__:\n{self.PrintPkmnDetails(self.targetpkmnchoice, self.targetdata)}\n\n__You Receive__:\n{self.PrintPkmnDetails(self.userpkmnchoice, self.userdata)}', 
				TradeColor)
			embed.set_thumbnail(url=self.botimg)
			self.message = await inter.followup.send(content=f'<@{self.targettrainer.UserId}>', embed=embed, view=self, ephemeral=False)
		else:
			if inter.user.id != self.targettrainer.UserId:
				return
			updatedTarget = trainerservice.GetTrainer(self.targettrainer.ServerId, self.targettrainer.UserId)
			targetPkmn = next((p for p in updatedTarget.OwnedPokemon if p.Id == self.targetpkmnchoice.Id), None)
			if not targetPkmn or targetPkmn.Pokemon_Id != self.targetpkmnchoice.Pokemon_Id:
				return await self.message.edit(content=f'The Pokemon being traded no longer exists. Please try again.', embed=None, view=None)
			trainerservice.TradePokemon(self.trainer, self.userpkmnchoice, updatedTarget, targetPkmn)
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			await self.message.edit(content=f'<@{self.user.id}> traded away **{pokemonservice.GetPokemonDisplayName(self.userpkmnchoice, self.userdata)}** to <@{updatedTarget.UserId}> for **{pokemonservice.GetPokemonDisplayName(targetPkmn, self.targetdata)}**', embed=None, view=None)

	def PrintPkmnDetails(self, pokemon: Pokemon, data: PokemonData):
		pkmnData = t2a(
			body=[
				['Level:', f"{pokemon.Level}{f'({pokemon.CurrentExp}/{pokemonservice.NeededExperience(pokemon.Level, data.Rarity, data.EvolvesInto)})' if pokemon.Level < 100 else ''}"], 
				['Height:', pokemon.Height],
				['Weight:', pokemon.Weight],
				['Color:',f"{data.Color}"],  
				['Types:', f"{data.Types[0]}"f"{'/' + data.Types[1] if len(data.Types) > 1 else ''}"]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"**{pokemonservice.GetPokemonDisplayName(pokemon, data)}**\n```{pkmnData}```"

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
