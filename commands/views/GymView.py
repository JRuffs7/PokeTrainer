import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from globals import BattleColor
from models.Gym import GymLeader
from services import gymservice
from services.utility import discordservice


class GymView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, leader: GymLeader,
							 userTeam: list[str], gymTeam: list[str], battleResults: list[int]):
		self.interaction = interaction
		self.user = interaction.user
		self.leader = leader
		self.userteam = userTeam
		self.gymteam = gymTeam
		self.battleresults = battleResults
		super().__init__(timeout=300)
    
	async def send(self):
		await self.interaction.response.send_message(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.user.display_name} vs {self.leader.Name}!",
				self.CreateEmbedDesc(), BattleColor)
		embed.set_thumbnail(url=self.leader.Sprite)
		badge = gymservice.GetBadgeById(self.leader.BadgeId)
		embed.set_footer(icon_url=badge.Sprite, text=f"{badge.Name} Badge")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
	async def next_button(self, inter: discord.Interaction,
										button: discord.ui.Button):
		await self.message.delete()
		await inter.response.send_message(content=f'Obtained the {gymservice.GetBadgeById(self.leader.BadgeId).Name} Badge!\nWon ${self.leader.Reward} and gained exp.',ephemeral=True)

	def CreateEmbedDesc(self):
		first = second = 0
		battleArr = []
		for res in self.battleresults:
			#Team One Wins
			if res == 1:
				battleArr.append([f"\u001b[0;37m{self.userteam[first]}\u001b[0m",f"\u001b[0;31m{self.gymteam[second]}\u001b[0m"])
				second += 1
			#Team Two Wins
			else:
				battleArr.append([f"\u001b[0;31m{self.userteam[first]}\u001b[0m",f"\u001b[0;37m{self.gymteam[second]}\u001b[0m"])
				first += 1
		
		battle = t2a(
			body=battleArr, 
			first_col_heading=False,
			alignments=Alignment.CENTER,
			style=PresetStyle.markdown,
			cell_padding=2)
		
		if first >= len(self.userteam):
			self.clear_items()
		return f"```ansi\n{battle}```\n{'You won!' if first < len(self.userteam) else 'You have been defeated.'}"
