import discord

from globals import TrainerColor, region_name
from middleware.decorators import defer
from models.Cpu import Badge
from models.Trainer import Trainer
from services import gymservice
from services.utility import discordservice


class BadgeView(discord.ui.View):

	def __init__(self, targetUser: discord.Member, trainer: Trainer, data: list[Badge], images: bool, region: int|None):
		self.targetuser = targetUser
		self.trainer = trainer
		self.data = data
		self.data.sort(key=lambda x: x.Id)
		self.images = images
		self.region = region
		self.currentpage = 1
		self.totalpages = len(self.data) if images else 1 if region else len(gymservice.GetRegions())
		super().__init__(timeout=300)
		self.firstbtn = discord.ui.Button(label="|<", style=discord.ButtonStyle.green, custom_id="first", disabled=True)
		self.firstbtn.callback = self.page_button
		self.prevbtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
		self.prevbtn.callback = self.page_button
		self.nextbtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, custom_id="next", disabled=(self.totalpages==1))
		self.nextbtn.callback = self.page_button
		self.lastbtn = discord.ui.Button(label=">|", style=discord.ButtonStyle.green, custom_id="last", disabled=(self.totalpages==1))
		self.lastbtn.callback = self.page_button
		self.add_item(self.firstbtn)
		self.add_item(self.prevbtn)
		self.add_item(self.nextbtn)
		self.add_item(self.lastbtn)

	async def update_message(self):
		usrBadges, totalBadges = gymservice.GymCompletion(self.trainer, self.region)
		embed = discordservice.CreateEmbed(
				f"{self.targetuser.display_name}'s{f' {region_name(self.region)}' if self.region else ''} Badges ({usrBadges}/{totalBadges})",
				self.SingleEmbedDesc() if self.images else self.ListEmbedDesc(),
				TrainerColor,
				image=(self.data[self.currentpage-1].Sprite if self.images else None),
				thumbnail=(self.targetuser.display_avatar.url if not self.images else None),
				footer=f"{self.currentpage}/{self.totalpages}")
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'first':
			self.currentpage = 1
		elif inter.data['custom_id'] == 'previous':
			self.currentpage -= 1
		elif inter.data['custom_id'] == 'next':
			self.currentpage += 1
		elif inter.data['custom_id'] == 'last':
			self.currentpage = self.totalpages

		self.firstbtn.disabled = self.currentpage == 1
		self.prevbtn.disabled = self.currentpage == 1
		self.lastbtn.disabled = self.currentpage == self.totalpages
		self.nextbtn.disabled = self.currentpage == self.totalpages
		await self.update_message()

	def SingleEmbedDesc(self):
		badge = self.data[self.currentpage-1]
		return f'**__{badge.Name} Badge__**\nRegion: {region_name(badge.Generation)}\nGym Leader: {gymservice.GetGymLeaderByBadge(badge.Id).Name}'

	def ListEmbedDesc(self):
		badges = self.data if self.region else [b for b in self.data if b.Generation == (self.currentpage if self.currentpage < self.totalpages else 1000)]
		badges.sort(key=lambda x: x.Id)
		newline = '\n'
		desc = f'__**{region_name(self.currentpage)}**__\n' if not self.region else ''
		if badges:
			return f"{desc}{newline.join([f'{b.Name} Badge' for b in badges])}"
		return f'{desc}No badges!'

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()