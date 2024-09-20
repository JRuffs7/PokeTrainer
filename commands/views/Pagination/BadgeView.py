from math import ceil
import discord
from commands.views.Pagination.BasePaginationView import BasePaginationView

from globals import TrainerColor, region_name
from models.Cpu import Badge
from services import gymservice
from services.utility import discordservice


class BadgeView(BasePaginationView):

	def __init__(self, interaction: discord.Interaction, targetUser: discord.Member, pageLength: int, title: str, data: list):
		self.title = title
		self.targetuser = targetUser
		super(BadgeView, self).__init__(interaction, pageLength, data)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
		await self.update_message(self.data[:self.pageLength])

	async def update_message(self, data: list[Badge]):
		self.update_buttons()
		embed = discordservice.CreateEmbed(
				self.title,
				self.SingleEmbedDesc(data[0]) if self.pageLength == 1 else self.ListEmbedDesc(data),
				TrainerColor)
		if self.pageLength == 1:
			embed.set_image(url=data[0].Sprite)
		else:
			embed.set_thumbnail(url=self.targetuser.display_avatar.url)
		embed.set_footer(text=f"{self.currentPage}/{ceil(len(self.data)/self.pageLength)}")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="|<", style=discord.ButtonStyle.green, custom_id="first")
	async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
	async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">|", style=discord.ButtonStyle.green, custom_id="last")
	async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	def SingleEmbedDesc(self, badge: Badge):
		return f'**__{badge.Name} Badge__**\nRegion: {region_name(badge.Generation)}\nGym Leader: {gymservice.GetGymLeaderByBadge(badge.Id).Name}'

	def ListEmbedDesc(self, data):
		newline = '\n'
		return f"{newline.join([f'{b.Name} Badge' for b in data])}"
