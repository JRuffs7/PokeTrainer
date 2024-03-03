from math import ceil
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import BattleColor
from models.Gym import GymLeader
from services import gymservice, pokemonservice
from services.utility import discordservice


class GymLeaderView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, leader: GymLeader, defeated: bool):
		self.interaction = interaction
		self.leader = leader
		self.defeated = defeated
		super().__init__()
		self.prev_button.disabled = True
		if not defeated:
			self.next_button.disabled = True

	async def send(self):
		if not self.leader:
			await self.interaction.response.send_message("The gym leader provided does not exist. Please try again.", ephemeral=True)
		await self.interaction.response.send_message(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message(False)

	async def update_message(self, showTeam: bool):
		embed = discordservice.CreateEmbed(
				self.leader.Name,
				self.GymLeaderDesc() if not showTeam else self.LeaderTeamDesc(),
				BattleColor)
		if not showTeam:
			embed.set_image(url=self.leader.Sprite)
		else:
			embed.set_thumbnail(url=self.leader.Sprite)
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
	async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.next_button.disabled = False
		self.prev_button.disabled = True
		await self.update_message(False)
		

	@discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.prev_button.disabled = False
		self.next_button.disabled = True
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
