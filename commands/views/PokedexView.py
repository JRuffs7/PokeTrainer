import discord

from globals import TrainerColor
from services.utility import discordservice


class PokedexView(discord.ui.View):

  def __init__(self, interaction: discord.Interaction, pageLength, user):
    self.interaction = interaction
    self.pageLength = pageLength
    self.user = user
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
    await self.interaction.response.send_message(view=self)
    self.message = await self.interaction.original_response()
    await self.update_message(self.data[:self.pageLength])

  async def update_message(self, data):
    self.update_buttons()
    if self.pageLength == 1:
      data = data[0]
    newline = '\n'
    embed = discordservice.CreateEmbed(
        f"{self.user.display_name}'s Pokedex",
        f"**__{data['Name']}__**{' :female_sign:' if data['Pokemon'].IsFemale == True else ' :male_sign:' if data['Pokemon'].IsFemale == False else ''}{' :sparkles:' if data['Pokemon'].IsShiny else ''}\nHeight: {data['Pokemon'].Height}\nWeight: {data['Pokemon'].Weight}\nTypes: {','.join(data['Types'])}"
        if self.pageLength == 1 else f"{newline.join(data)}", TrainerColor)
    if self.pageLength == 1:
      embed.set_image(url=data['Image'])
    else:
      embed.set_thumbnail(url=self.user.display_avatar.url)
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
