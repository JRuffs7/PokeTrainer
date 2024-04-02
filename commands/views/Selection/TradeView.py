import discord
from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge
from globals import TradeColor
from middleware.decorators import button_check

from models.Trainer import Trainer
from services import trainerservice, pokemonservice
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
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(self.usertradelist, 1, customId='ownedTradeList')
		self.targetlist = OwnedSelector(self.targettradelist, 1, customId='targetTradeList')
		self.add_item(self.ownlist)
		self.add_item(self.targetlist)


	@button_check
	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		await inter.response.defer()
		if inter.data['custom_id'] == 'ownedTradeList':
			self.userpkmnchoice = next(p for p in self.usertradelist if p.Id == choice[0])
		else:
			self.targetpkmnchoice = next(p for p in self.targettradelist if p.Id == choice[0])

	@discord.ui.button(label='Reject', style=discord.ButtonStyle.red)
	async def cancel_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await inter.response.defer()
		if self.initial:
			if inter.user.id != self.trainer.UserId:
				return
			self.clear_items()
			await self.message.edit(content='Trade canceled.', view=self)
		else:
			if inter.user.id != self.targettrainer.UserId:
				return
			self.clear_items()
			await self.message.delete()
			await inter.followup.send(content=f'<@{self.user.id}>\nTrade offer was rejected.', embed=None, view=self)


	@discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await inter.response.defer()
		if self.initial:
			if not self.userpkmnchoice or not self.targetpkmnchoice or inter.user.id != self.trainer.UserId:
				return
		
			await self.message.delete()
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
			await self.message.delete()
			trainerservice.TradePokemon(self.trainer, self.userpkmnchoice, self.targettrainer, self.targetpkmnchoice)
			await inter.followup.send(content=f'<@{self.user.id}> traded away **{pokemonservice.GetPokemonDisplayName(self.userpkmnchoice, self.userdata)}** to <@{self.targettrainer.UserId}> for **{pokemonservice.GetPokemonDisplayName(self.targetpkmnchoice, self.targetdata)}**')


	def PrintPkmnDetails(self, pokemon: Pokemon, data: PokemonData):
		pkmnData = t2a(
			body=[
				['Level:', f"{pokemon.Level}{f'({pokemon.CurrentExp}/{pokemonservice.NeededExperience(pokemon.Level, data.Rarity, len(data.EvolvesInto) > 0)})' if pokemon.Level < 100 else ''}"], 
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
