from math import ceil
import discord
from table2ascii import Alignment, Merge, PresetStyle, table2ascii as t2a

from globals import Dexmark, TrainerColor, region_name
from middleware.decorators import defer
from models.Pokemon import PokemonData
from models.Trainer import Trainer
from services import statservice
from services.utility import discordservice


class PokedexView(discord.ui.View):

	def __init__(self, targetUser: discord.User|discord.Member, trainer: Trainer, dexType: int|None, single: bool, data: list[PokemonData]):
		self.targetuser = targetUser
		self.trainer = trainer
		self.dex = dexType
		self.single = single
		self.data = data
		self.currentPage = 1
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
		data = self.get_currentPage_data()
		dexCompletion = f'({len(self.trainer.Pokedex) if not self.dex else len(self.trainer.Formdex) if self.dex == 1 else len(self.trainer.Shinydex)}/{len(set(p.PokedexId for p in self.data)) if not self.dex else len(self.data) if not self.single else 1})'
		embed = discordservice.CreateEmbed(
				f"{self.targetuser.display_name}'s {'Pokedex' if not self.dex else 'Form Dex' if self.dex == 1 else 'Shiny Dex'} {dexCompletion}",
				self.SingleEmbedDesc(data[0]) if self.single else self.ListEmbedDesc(data),
				TrainerColor)
		if self.single:
			embed.set_image(url=data[0].Sprite if self.currentPage == 1 else data[0].ShinySprite if self.currentPage == 2 else data[0].SpriteFemale if self.currentPage == 3 else data[0].ShinySpriteFemale)
		else:
			embed.set_thumbnail(url=self.targetuser.display_avatar.url)
		embed.set_footer(text=f"{self.currentPage}/{ceil(len(self.data)/(1 if self.single else 10))}")
		await self.message.edit(embed=embed, view=self)

	def get_currentPage_data(self):
		until_item = self.currentPage * (1 if self.single else 10)
		from_item = until_item - (1 if self.single else 10)
		if self.currentPage == ceil(len(self.data)/(1 if self.single else 10)):
			until_item = len(self.data)
		return self.data[from_item:until_item]
	
	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'first':
			self.currentPage = 1
		elif inter.data['custom_id'] == 'previous':
			self.currentPage -= 1
		elif inter.data['custom_id'] == 'next':
			self.currentPage += 1
		elif inter.data['custom_id'] == 'last':
			self.currentPage = ceil(len(self.data)/(1 if self.single else 10))

		self.firstbtn.disabled = self.currentPage == 1
		self.prevbtn.disabled = self.currentPage == 1
		self.lastbtn.disabled = self.currentPage == ceil(len(self.data)/(1 if self.single else 10))
		self.nextbtn.disabled = self.currentPage == ceil(len(self.data)/(1 if self.single else 10))
		await self.update_message()

	def SingleEmbedDesc(self, pokemon: PokemonData):
		trainerdex = self.trainer.Pokedex if not self.dex else self.trainer.Formdex
		growth = '^' if pokemon.GrowthRate == 'fluctuating' else '^^' if pokemon.GrowthRate == 'slow' else '^^^' if pokemon.GrowthRate == 'mediumslow' else '^^^^' if pokemon.GrowthRate == 'medium' else '^^^^^' if pokemon.GrowthRate == 'fast' else '^^^^^^'
		pkmnData = t2a(body=[['Pokedex:', pokemon.PokedexId, '|', 'Height:', pokemon.Height/10],
											 	 ['Region:', region_name(pokemon.Generation), '|', 'Weight:', pokemon.Weight/10],
                         ['Color:',pokemon.Color, '|','Growth:', growth], 
                         ['Capture:',f'{pokemon.CaptureRate}/255', '|','Female:', f'{pokemon.FemaleChance}/8' if pokemon.FemaleChance >= 0 else 'N/A'], 
                         ['Types:', f'{"/".join([statservice.GetType(t).Name for t in pokemon.Types])}', Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0) if pokemon.PokedexId in self.trainer.Pokedex else ''
		dataString = f'\n```{pkmnData}```' if pkmnData else ''
		if self.currentPage in [1,3]:
			return f"**__{pokemon.Name}__** {Dexmark if (pokemon.PokedexId if not self.dex else pokemon.Id) in trainerdex else ''}{dataString}"
		return f"**__{pokemon.Name}__** {Dexmark if pokemon.Id in self.trainer.Shinydex else ''}{dataString}"

	def ListEmbedDesc(self, data: list[PokemonData]):
		trainerdex = self.trainer.Pokedex if not self.dex else self.trainer.Formdex if self.dex == 1 else self.trainer.Shinydex
		dexList = [f'{x.Name} {Dexmark if (x.PokedexId if not self.dex else x.Id) in trainerdex else ""}' for x in data]
		return '\n'.join(dexList)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()