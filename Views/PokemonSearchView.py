from math import ceil
import discord

from globals import PokemonColor
from middleware.decorators import defer
from models.Pokemon import PokemonData
from services import statservice
from services.utility import discordservice


class PokemonSearchView(discord.ui.View):

  def __init__(self, dataList: list[PokemonData], type: int):
    self.data = dataList
    self.type = statservice.GetType(type)
    self.currentpage = 1
    self.totalpages = ceil(len(dataList)/10)
    super().__init__(timeout=300)
    self.firstbtn = discord.ui.Button(label="|<", style=discord.ButtonStyle.green, custom_id="first", disabled=True)
    self.firstbtn.callback = self.page_button
    self.prevbtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
    self.prevbtn.callback = self.page_button
    self.nextbtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
    self.nextbtn.callback = self.page_button
    self.lastbtn = discord.ui.Button(label=">|", style=discord.ButtonStyle.green, custom_id="last")
    self.lastbtn.callback = self.page_button
    self.add_item(self.firstbtn)
    self.add_item(self.prevbtn)
    self.add_item(self.nextbtn)
    self.add_item(self.lastbtn)

  async def update_message(self):
    self.update_buttons()
    embed = discordservice.CreateEmbed(
      f'List of {self.type.Name} Type Pokemon', 
      self.EmbedDesc(), 
      PokemonColor)
    embed.set_footer(text=f"{self.currentpage}/{self.totalpages}")
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

    self.firstbtn.disabled = self.currentpage == 0
    self.prevbtn.disabled = self.currentpage == 0
    self.lastbtn.disabled = self.currentpage == self.totalpages
    self.nextbtn.disabled = self.currentpage == self.totalpages
    await self.update_message()

  def EmbedDesc(self):
    dataList = self.data[(10*self.currentpage-1):(10*self.currentpage)]
    newline = '\n'
    slash = '/'
    return f"{newline.join([f'**{x.Name}** ({slash.join([statservice.GetType(t).Name for t in x.Types])})' for x in dataList])}"

  async def send(self, inter: discord.Interaction):
    await inter.followup.send(view=self)
    self.message = await self.interaction.original_response()
    await self.update_message()