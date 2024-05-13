import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import BattleColor
from middleware.decorators import defer
from models.Gym import GymLeader
from services import gymservice, pokemonservice
from services.utility import discordservice


class GymLeaderView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, leader: GymLeader, showTeam: bool):
		self.interaction = interaction
		self.leader = leader
		self.badge = gymservice.GetBadgeById(leader.BadgeId)
		self.currentpage = 1
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

	async def send(self):
		if not self.leader:
			await self.interaction.followup.send("The gym leader provided does not exist. Please try again.", ephemeral=True)
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		teamView = self.currentpage == 2
		embed = discordservice.CreateEmbed(
				self.leader.Name if not teamView else f"{self.leader.Name}'s Team",
				self.GymLeaderDesc() if not teamView else self.LeaderTeamDesc(),
				BattleColor)
		if not teamView:
			embed.set_image(url=self.leader.Sprite)
			embed.set_thumbnail(url=self.badge.Sprite)
		else:
			embed.set_thumbnail(url=self.leader.Sprite)
		embed.set_footer(icon_url=self.badge.Sprite, text=f"{self.badge.Name} Badge")
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, interaction: discord.Interaction):
		self.currentpage = 1 if interaction.data['custom_id'] == 'prev' else 2
		self.prevBtn.disabled = self.currentpage == 1
		self.nextBtn.disabled = self.currentpage == 2
		await self.update_message()

	def GymLeaderDesc(self):
		badge = gymservice.GetBadgeById(self.leader.BadgeId)
		ldrData = t2a(body=[['Gym Type:', f"{self.leader.MainType}"],
												['Reward:', self.leader.Reward]], 
											first_col_heading=False,
											alignments=[Alignment.LEFT,Alignment.LEFT],
											style=PresetStyle.plain,
											cell_padding=0)
		return f"```{ldrData}```"

	def LeaderTeamDesc(self):
		newline = '\n'
		return f"{newline.join([pokemonservice.GetPokemonById(x).Name for x in self.leader.Team])}"
