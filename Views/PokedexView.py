from math import ceil
import discord
from table2ascii import Alignment, Merge, PresetStyle, table2ascii as t2a

from globals import Dexmark, TrainerColor, region_name
from middleware.decorators import defer
from models.Pokemon import PokemonData
from models.Trainer import Trainer
from services import itemservice, moveservice, pokemonservice, statservice
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

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		data = self.get_currentPage_data()
		dexCompletion = f'({len(self.trainer.Pokedex) if not self.dex else len(self.trainer.Formdex) if self.dex == 1 else len(self.trainer.Shinydex)}/{len(set(p.PokedexId for p in self.data)) if not self.dex else len(self.data) if not self.single else 1})'
		if self.single:
			dexCompletion = f'{"1" if data.PokedexId in self.trainer.Pokedex else "0"}/1'
			if self.currentPage <= len([i for i in [data.Sprite, data.ShinySprite, data.SpriteFemale, data.ShinySpriteFemale] if i]):
				image = data.Sprite if self.currentPage == 1 else data.ShinySprite if self.currentPage == 2 else data.SpriteFemale if self.currentPage == 3 else data.ShinySpriteFemale
			else:
				image = None
		else:
			dexCompletion = f'({len(self.trainer.Pokedex) if not self.dex else len(self.trainer.Formdex) if self.dex == 1 else len(self.trainer.Shinydex)}/{len(set(p.PokedexId for p in self.data)) if not self.dex else len(self.data) if not self.single else 1})'
			image = None
		embed = discordservice.CreateEmbed(
				f"{self.targetuser.display_name}'s {'Pokedex' if not self.dex else 'Form Dex' if self.dex == 1 else 'Shiny Dex'} {dexCompletion}",
				self.SingleEmbedDesc(data) if self.single else self.ListEmbedDesc(data),
				TrainerColor,
				image=image,
				thumbnail=(self.targetuser.display_avatar.url if not self.single else None),
				footer=f'{self.currentPage}/{ceil(len(self.data)/(1 if self.single else 10))}')
		await self.message.edit(embed=embed, view=self)

	def get_currentPage_data(self):
		if self.single:
			return self.data[0]
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
		if self.currentPage < len(self.data):
			trainerdex = self.trainer.Pokedex if not self.dex else self.trainer.Formdex
			pkmnData = t2a(
				body=[
					['Pokedex:', pokemon.PokedexId, '|', 'Height:', pokemon.Height/10],
					['Region:', region_name(pokemon.Generation), '|', 'Weight:', pokemon.Weight/10],
					['Color:',pokemon.Color, '|','Female:', f'{pokemon.FemaleChance}/8' if pokemon.FemaleChance >= 0 else 'N/A'], 
					['Types:', f'{"/".join([statservice.GetType(t).Name for t in pokemon.Types])}', Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
				first_col_heading=False,
				alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
				style=PresetStyle.plain,
				cell_padding=0) if pokemon.PokedexId in self.trainer.Pokedex else ''
			dataString = f'\n```{pkmnData}```' if pkmnData else ''
			if self.currentPage in [1,3]:
				return f"**__{pokemon.Name}__** {Dexmark if (pokemon.PokedexId if not self.dex else pokemon.Id) in trainerdex else ''}{dataString}"
			return f"**__{pokemon.Name}__** {Dexmark if pokemon.Id in self.trainer.Shinydex else ''}{dataString}"
		else:
			evolveArr: list[list[str]] = []
			for e in pokemon.EvolvesInto:
				evData = pokemonservice.GetPokemonById(e.EvolveID)
				if evolveArr:
					evolveArr.append([''])
				evolveArr.append([evData.Name])
				evolveArr.append([''.join(['-' for _ in evData.Name])])
				if e.EvolveLevel:
					evolveArr.append([f'Level:  {e.EvolveLevel}'])
				if e.GenderNeeded:
					evolveArr.append([f'Gender: {"Female" if e.GenderNeeded == 1 else "Male"}'])
				if e.ItemNeeded:
					evolveArr.append([f'Item:   {itemservice.GetItem(e.ItemNeeded).Name}'])
				if e.MoveNeeded:
					evolveArr.append([f'Move:   {moveservice.GetMoveById(e.MoveNeeded).Name}'])
			if not evolveArr:
				evolveArr.append([f'This Pokemon does not evolve.'])
			pkmnData = t2a(
				body=evolveArr, 
				first_col_heading=False,
				alignments=[Alignment.LEFT],
				style=PresetStyle.plain,
				cell_padding=0,
				column_widths=[max([len(e[0]) for e in evolveArr])])
			return f"**__{pokemon.Name} Evolutions__**\n\n```{pkmnData}```"

	def ListEmbedDesc(self, data: list[PokemonData]):
		trainerdex = self.trainer.Pokedex if not self.dex else self.trainer.Formdex if self.dex == 1 else self.trainer.Shinydex
		dexList = [f'{x.Name} {Dexmark if (x.PokedexId if not self.dex else x.Id) in trainerdex else ""}' for x in data]
		return '\n'.join(dexList)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()