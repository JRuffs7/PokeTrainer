import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import BattleColor
from middleware.decorators import defer
from models.Gym import GymLeader
from services import gymservice, pokemonservice
from services.utility import discordservice


class GymLeaderView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, leader: GymLeader, defeated: bool):
		self.interaction = interaction
		self.leader = leader
		self.defeated = defeated
		super().__init__()
		self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
		self.prevBtn.callback = self.page_button
		self.add_item(self.prevBtn)
		self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
		self.nextBtn.callback = self.page_button
		self.add_item(self.nextBtn)
		self.prevBtn.disabled = True
		if not defeated:
			self.nextBtn.disabled = True

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def send(self):
		if not self.leader:
			await self.interaction.followup.send("The gym leader provided does not exist. Please try again.", ephemeral=True)
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message(False)

	async def update_message(self, showTeam: bool):
		embed = discordservice.CreateEmbed(
				self.leader.Name if not showTeam else f"{self.leader.Name}'s Team",
				self.GymLeaderDesc() if not showTeam else self.LeaderTeamDesc(),
				BattleColor)
		if not showTeam:
			embed.set_image(url=self.leader.Sprite)
		else:
			embed.set_thumbnail(url=self.leader.Sprite)
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, interaction: discord.Interaction):
		if interaction.data['custom_id'] == 'prev':
			self.prevBtn.disabled = True
			self.nextBtn.disabled = False
			await self.update_message(False)
		else:
			self.prevBtn.disabled = False
			self.nextBtn.disabled = True
			await self.update_message(True)

	def GymLeaderDesc(self):
		badge = gymservice.GetBadgeById(self.leader.BadgeId)
		ldrData = t2a(body=[['Badge:', badge.Name, '|', 'Reward:', self.leader.Reward], 
												 ['Gym Type:', f"{self.leader.MainType}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
											first_col_heading=False,
											alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
											style=PresetStyle.plain,
											cell_padding=0)
		return f"```{ldrData}```"

	def LeaderTeamDesc(self):
		newline = '\n'
		return f"{newline.join([pokemonservice.GetPokemonById(x).Name for x in self.leader.Team])}"
