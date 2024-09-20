import discord

from table2ascii import Merge, table2ascii as t2a, PresetStyle, Alignment

from globals import BattleColor
from middleware.decorators import defer
from models.Cpu import CpuTrainer
from models.Pokemon import Pokemon
from services import gymservice, moveservice, pokemonservice, statservice
from services.utility import discordservice


class GymLeaderView(discord.ui.View):

	def __init__(self, leader: CpuTrainer, showTeam: bool):
		self.leader = leader
		self.badge = gymservice.GetBadgeById(leader.BadgeId)
		self.currentpage = 1
		self.maxpage = len(leader.Team) + 1
		super().__init__()
		self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
		self.prevBtn.callback = self.page_button
		self.add_item(self.prevBtn)
		self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
		self.nextBtn.callback = self.page_button
		self.add_item(self.nextBtn)
		self.prevBtn.disabled = True
		if not showTeam:
			self.nextBtn.disabled = True

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self, ephemeral=True)
		self.message = await inter.original_response()
		await self.update_message()

	async def update_message(self):
		leaderView = self.currentpage == 1
		embed = discordservice.CreateEmbed(
				self.leader.Name if leaderView else f"{self.leader.Name}'s Team",
				self.GymLeaderDesc() if leaderView else self.PokemonDesc(self.leader.Team[self.currentpage-2]),
				BattleColor)
		if leaderView:
			embed.set_image(url=self.leader.Sprite)
			embed.set_thumbnail(url=self.badge.Sprite)
		else:
			embed.set_image(url=pokemonservice.GetPokemonImage(self.leader.Team[self.currentpage-2]))
		embed.set_footer(icon_url=self.badge.Sprite, text=f"{self.badge.Name} Badge")
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, interaction: discord.Interaction):
		if interaction.data['custom_id'] == 'prev':
			self.currentpage -= 1
		else:
			self.currentpage += 1
		self.prevBtn.disabled = self.currentpage == 1
		self.nextBtn.disabled = self.currentpage == self.maxpage
		await self.update_message()

	def GymLeaderDesc(self):
		ldrData = t2a(
			body=[
				['Badge:', self.badge.Name],
				['Gym Type:', f"{self.leader.MainType}"],
				['Reward:', f'${self.leader.Reward[1]}']], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"```{ldrData}```"
	
	def PokemonDesc(self, pokemon: Pokemon):
		data = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		move0 = moveservice.GetMoveById(pokemon.LearnedMoves[0].MoveId).Name
		move1 = moveservice.GetMoveById(pokemon.LearnedMoves[1].MoveId).Name if len(pokemon.LearnedMoves) > 1 else ''
		move2 = moveservice.GetMoveById(pokemon.LearnedMoves[2].MoveId).Name if len(pokemon.LearnedMoves) > 2 else ''
		move3 = moveservice.GetMoveById(pokemon.LearnedMoves[3].MoveId).Name if len(pokemon.LearnedMoves) > 3 else ''
		pkmnData = t2a(
			body=[
				[move0,'|',move1],
				[move2,'|',move3],
				[f'Types: {"/".join([statservice.GetType(t).Name for t in data.Types])}', Merge.LEFT, Merge.LEFT]
			], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.CENTER,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"**__{pokemonservice.GetPokemonDisplayName(pokemon, data)} (Lvl. {pokemon.Level})__**\n```{pkmnData}```"

	def LeaderTeamDesc(self):
		newline = '\n'
		return f"{newline.join([pokemonservice.GetPokemonById(x).Name for x in self.leader.Team])}"
