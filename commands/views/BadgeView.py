import discord

from globals import TrainerColor, region_name
from services.utility import discordservice


class BadgeView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, pageLength, title):
		self.interaction = interaction
		self.pageLength = pageLength
		self.title = title
		self.currentPage = 1
		self.addition = 1 if self.pageLength > 1 else 0
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

		if self.currentPage == int(
				len(self.data) / self.pageLength) + self.addition:
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
		if self.currentPage == 1:
			from_item = 0
			until_item = self.pageLength
		if self.currentPage == int(
				len(self.data) / self.pageLength) + self.addition:
			from_item = self.currentPage * self.pageLength - self.pageLength
			until_item = len(self.data)
		return self.data[from_item:until_item]

	async def send(self):
		if not self.data:
			await self.interaction.response.send_message("You do not own any Badges.", ephemeral=True)
		else:
			await self.interaction.response.send_message(view=self, ephemeral=True)
			self.message = await self.interaction.original_response()
			await self.update_message(self.data[:self.pageLength])

	async def update_message(self, data):
		self.update_buttons()
		if self.pageLength == 1:
			data = data[0]
		embed = discordservice.CreateEmbed(
				self.title,
				self.CreateEmbedDesc(data), TrainerColor)
		if self.pageLength == 1:
			print(data.Sprite)
			embed.set_image(url=data.Sprite)
		else:
			embed.set_thumbnail(url=self.user.display_avatar.url)
		embed.set_footer(text=f"{self.currentPage}/{int(len(self.data)/self.pageLength)+self.addition}")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="|<", style=discord.ButtonStyle.green)
	async def first_page_button(self, interaction: discord.Interaction,
															button: discord.ui.Button):
		await interaction.response.defer()
		self.currentPage = 1

		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label="<", style=discord.ButtonStyle.primary)
	async def prev_button(self, interaction: discord.Interaction,
												button: discord.ui.Button):
		await interaction.response.defer()
		self.currentPage -= 1
		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">", style=discord.ButtonStyle.primary)
	async def next_button(self, interaction: discord.Interaction,
												button: discord.ui.Button):
		await interaction.response.defer()
		self.currentPage += 1
		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">|", style=discord.ButtonStyle.green)
	async def last_page_button(self, interaction: discord.Interaction,
															button: discord.ui.Button):
		await interaction.response.defer()
		self.currentPage = int(len(self.data) / self.pageLength) + self.addition
		await self.update_message(self.get_currentPage_data())


	def CreateEmbedDesc(self, data):
		newline = '\n'
		if self.pageLength == 1:
			return f'**__{data.Name} Badge__**\nRegion: {region_name(data.Generation)}'
		return f"{newline.join([b.Name + ' Badge' for b in data])}"
