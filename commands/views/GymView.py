import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from globals import BattleColor
from middleware.decorators import button_check
from models.Gym import GymLeader
from models.Trainer import Trainer
from services import gymservice, trainerservice
from services.utility import discordservice


class GymView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, leader: GymLeader,
							 trainer: Trainer, battleResults: list[bool]):
		self.interaction = interaction
		self.user = interaction.user
		self.leader = leader
		self.leaderTeam = gymservice.GetBattleTeam(leader.Team)
		self.trainerTeam = gymservice.GetBattleTeam([p.Pokemon_Id for p in trainerservice.GetTeam(trainer) if p])
		self.battleresults = battleResults
		self.battlewon = battleResults.count(True) == len(self.leader.Team)
		super().__init__(timeout=300)
    
	async def send(self):
		await self.interaction.response.send_message(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.user.display_name} VS {self.leader.Name}!",
				self.CreateEmbedDesc(), BattleColor)
		embed.set_thumbnail(url=self.leader.Sprite)
		badge = gymservice.GetBadgeById(self.leader.BadgeId)
		embed.set_footer(icon_url=badge.Sprite, text=f"{badge.Name} Badge")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
	@button_check
	async def next_button(self, inter: discord.Interaction,
										button: discord.ui.Button):
		await self.message.delete()
		if self.battlewon:
			await inter.response.send_message(content=f'<@{self.interaction.user.display_name}> defeated {self.leader.Name} and obtained the {gymservice.GetBadgeById(self.leader.BadgeId).Name} Badge!\nWon ${self.leader.Reward} and gained exp.')
		else:
			await inter.response.send_message(content=f'<@{self.interaction.user.display_name}> was defeated by {self.leader.Name}.\nLost ${int(self.leader.Reward/2)}.')

	def CreateEmbedDesc(self):
		first = second = 0
		battleArr = []
		for res in self.battleresults:
			#Team One Wins
			if res:
				battleArr.append([f"\u001b[0;37m{self.trainerTeam[first].Name}\u001b[0m",f"\u001b[0;31m{self.leaderTeam[second].Name}\u001b[0m"])
				second += 1
			#Team Two Wins
			else:
				battleArr.append([f"\u001b[0;31m{self.trainerTeam[first].Name}\u001b[0m",f"\u001b[0;37m{self.leaderTeam[second].Name}\u001b[0m"])
				first += 1
		
		battle = t2a(
			body=battleArr, 
			first_col_heading=False,
			alignments=Alignment.CENTER,
			style=PresetStyle.markdown,
			cell_padding=2)
		
		return f"```ansi\n{battle}```\n{'You won!' if first < len(self.trainerTeam) else 'You have been defeated.'}"
