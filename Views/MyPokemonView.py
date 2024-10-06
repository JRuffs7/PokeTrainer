from math import ceil, floor
import discord

from commands.views.Pagination.BasePaginationView import BasePaginationView
from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import TrainerColor
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import itemservice, pokemonservice, statservice
from services.utility import discordservice


class MyPokemonView(discord.ui.View):

  def __init__(self, trainer: Trainer, data: list[Pokemon], images: bool, title: str, order: str|None = None, thumbnail: str|None = None):
    self.trainer = trainer
    self.data = data
    self.images = images
    self.title = title
    self.order = order
    self.thumbnail = thumbnail
    self.pokemondata = pokemonservice.GetPokemonByIdList([d.Pokemon_Id for d in data])
    self.currentpage = 1
    self.totalpages = len(self.data) if images else ceil(len(self.data)/10)
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

  async def on_timeout(self):
    await self.message.delete(delay=0.1)
    return await super().on_timeout()

  async def update_message(self):
    data = self.get_currentpage_data()
    if self.images:
      image = pokemonservice.GetPokemonImage(data[0], next(p for p in self.pokemondata if p.Id == data[0].Pokemon_Id))
      ball = itemservice.GetPokeball(data[0].CaughtBy)
      footerIcon = ball.Sprite if ball.Sprite else None
      footer = ball.Name
    else:
      image = None
      footerIcon = None
      footer = f'{self.currentpage}/{self.totalpages}'
      
    embed = discordservice.CreateEmbed(
        self.title,
        self.SingleEmbedDesc(data[0]) if self.images else self.ListEmbedDesc(data),
        TrainerColor,
        image=image,
        thumbnail=(self.thumbnail if not self.images else None),
        footerIcon=footerIcon,
        footer=footer)
    await self.message.edit(embed=embed, view=self)

  def get_currentpage_data(self):
    start = (1 if self.images else 10) * (self.currentpage-1)
    end = (1 if self.images else 10) * self.currentpage
    return self.data[start:end]

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

  def SingleEmbedDesc(self, pokemon: Pokemon):
    data = next(p for p in self.pokemondata if p.Id == pokemon.Pokemon_Id)
    pkmnData = t2a(
      body=[
        ['Level:', pokemon.Level, '|', 'HP:', statservice.GenerateStat(pokemon, data, StatEnum.HP)],
        ['Exp:', f'{pokemon.CurrentExp} ({floor(pokemon.CurrentExp*100/pokemonservice.NeededExperience(pokemon, data))}%)' if pokemon.Level < 100 else '-', '|', 'Att:', statservice.GenerateStat(pokemon, data, StatEnum.Attack)],
        ['Nature:', statservice.GetNature(pokemon.Nature).Name, '|', 'Def:', statservice.GenerateStat(pokemon, data, StatEnum.Defense)],
        ['IV Sum:', f'{sum([pokemon.IVs[i] for i in pokemon.IVs])}/{31*6}', '|', 'SpAt:', statservice.GenerateStat(pokemon, data, StatEnum.SpecialAttack)],
        ['Height:', pokemon.Height, '|', 'SpDe:', statservice.GenerateStat(pokemon, data, StatEnum.SpecialDefense)],
        ['Weight:', pokemon.Weight, '|', 'Spd:', statservice.GenerateStat(pokemon, data, StatEnum.Speed)],
        ['Types:', f'{"/".join([statservice.GetType(t).Name for t in data.Types])}', Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
      first_col_heading=False,
      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
      style=PresetStyle.plain,
      cell_padding=0)
    return f'**__{pokemonservice.GetPokemonDisplayName(pokemon, data)}__**\n```{pkmnData}```'

  def ListEmbedDesc(self, data: list[Pokemon]):
    namingArray = []
    for x in data:
      pkmnData = next(p for p in self.pokemondata if p.Id == x.Pokemon_Id)
      if self.order == 'height':
        detailStr = f'({x.Height}m)'
      elif self.order == 'weight':
        detailStr = f'({x.Weight}kg)'
      elif self.order == 'dex':
        detailStr = f'#{pkmnData.PokedexId}'
      else:
        detailStr = f'(Lvl. {x.Level})'
      namingArray.append(pokemonservice.GetPokemonDisplayName(x, pkmnData) + f' {detailStr}')
    newline = '\n'
    return f"{newline.join(namingArray)}"

  async def send(self, inter: discord.Interaction):
    await inter.followup.send(view=self)
    self.message = await inter.original_response()
    await self.update_message()
