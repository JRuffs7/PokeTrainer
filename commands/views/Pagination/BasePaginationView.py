from math import ceil
import discord

from middleware.decorators import defer


class BasePaginationView(discord.ui.View):

	def __init__(self, pageLength: int, dataList: list):
		self.pageLength = pageLength
		self.data = dataList
		self.currentPage = 1
		super().__init__(timeout=300)
		if pageLength*2 == len(dataList):
			self.first_page_button.disabled = True
			self.last_page_button.disabled = True
		elif pageLength >= len(dataList):
			self.first_page_button.disabled = True
			self.prev_button.disabled = True
			self.next_button.disabled = True
			self.last_page_button.disabled = True

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

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

	@defer
	async def button_click(self, interaction: discord.Interaction, custom_id: str):
		if interaction.user.id != self.user.id:
			return False
		match custom_id:
			case "next":
				self.currentPage += 1
			case "previous":
				self.currentPage -= 1
			case "last":
				self.currentPage = ceil(len(self.data)/self.pageLength)
			case _:
				self.currentPage = 1
		return True