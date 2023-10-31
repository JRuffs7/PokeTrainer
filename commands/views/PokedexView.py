import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import TrainerColor
from services import pokemonservice
from services.utility import discordservice


class PokedexView(discord.ui.View):

  def __init__(self, interaction: discord.Interaction, pageLength, user, title):
    self.interaction = interaction
    self.pageLength = pageLength
    self.user = user
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
      embed.set_image(url=data.Sprite)
    elif self.pageLength > 1 and self.user:
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
    if self.user:
      if self.pageLength == 1:
        pkmnData = t2a(body=[['CurrentExp:', f"{data.Pokemon.CurrentExp}/{(50 * data.Pokemon.Rarity) if data.Pokemon.Rarity <= 3 else 250}", '|', 'Height:', data.Pokemon.Height],
                            ['Can Evolve:',f"{'Yes' if pokemonservice.CanTrainerPokemonEvolve(data.Pokemon) else 'No'}", '|','Weight:', data.Pokemon.Weight], 
                            ['Types:', f"{data.Types[0]}"f"{'/' + data.Types[1] if len(data.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0)
        return f"**__{data.GetNameString()} (Lvl. {data.Pokemon.Level})__**\n```{pkmnData}```"
      return f"{newline.join([x.GetNameString() + '(Lvl. ' + x.Level + ')' for x in data])}"
    return f"**__{data.Name}__**\nAvg. Height: {data.Height}\nAvg. Weight: {data.Weight}\nTypes: {','.join(data.Types)}" if self.pageLength == 1 else f"{newline.join([x.Name for x in data])}"
