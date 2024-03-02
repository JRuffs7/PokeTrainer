from math import ceil
import discord

from middleware.decorators import button_check


class BasePaginationView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, pageLength: int, dataList: list):
		self.interaction = interaction
		self.user = interaction.user
		self.pageLength = pageLength
		self.data = dataList
		self.currentPage = 1
		super().__init__(timeout=300)

	def update_buttons(self):
		if self.currentPage == 1:
			self.first_page_button.disabled = True
			self.prev_button.disabled = True
			self.first_page_button.style = discord.ButtonStyle.gray
			self.prev_button.style = discord.ButtonStyle.gray
		else:
			self.first_page_button.disabled = False
			self.prev_button.disabled = False
			self.first_page_button.style = discord.ButtonStyle.green
			self.prev_button.style = discord.ButtonStyle.primary

		if self.currentPage == ceil(len(self.data)/self.pageLength):
			self.next_button.disabled = True
			self.last_page_button.disabled = True
			self.last_page_button.style = discord.ButtonStyle.gray
			self.next_button.style = discord.ButtonStyle.gray
		else:
			self.next_button.disabled = False
			self.last_page_button.disabled = False
			self.last_page_button.style = discord.ButtonStyle.green
			self.next_button.style = discord.ButtonStyle.primary

	def get_currentPage_data(self):
		until_item = self.currentPage * self.pageLength
		from_item = until_item - self.pageLength
		if self.currentPage == ceil(len(self.data)/self.pageLength):
			until_item = len(self.data)
		return self.data[from_item:until_item]

	@button_check
	async def button_click(self, interaction: discord.Interaction, custom_id: str):
		await interaction.response.defer()
		match custom_id:
			case "next":
				self.currentPage += 1
			case "previous":
				self.currentPage -= 1
			case "last":
				self.currentPage = ceil(len(self.data)/self.pageLength)
			case _:
				self.currentPage = 1