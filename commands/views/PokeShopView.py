import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import Dexmark, PokemonColor
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from services.utility import discordservice


class PokeShopView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer, pokemon: Pokemon):
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		self.price = pokemonservice.GetShopValue(self.pkmndata)*(2 if self.pokemon.IsShiny else 1)
		self.masterballs = 20 if not self.pokemon.IsShiny else 30
		super().__init__()

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def send(self):
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f'${self.price} + {self.masterballs}x Masterball',
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url= pokemonservice.GetPokemonImage(self.pokemon, self.pkmndata))
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(style=discord.ButtonStyle.red ,label='Cancel')
	@defer
	async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(view=self, embed=None, content='Left the PokeShop.')

	@discord.ui.button(style=discord.ButtonStyle.green ,label='Confirm')
	@defer
	async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		self.clear_items()
		updateTrainer = trainerservice.GetTrainer(self.trainer.ServerId, self.trainer.UserId)
		if updateTrainer.Money < self.price:
			return await self.message.edit(view=self, embed=None, content='Not enough money for an exchange.')
		if "4" not in updateTrainer.Pokeballs or updateTrainer.Pokeballs["4"] < self.masterballs:
			return await self.message.edit(view=self, embed=None, content='Not enough Masterballs for an exchange.')
		
		updateTrainer.OwnedPokemon.append(self.pokemon)
		updateTrainer.Money -= self.price
		trainerservice.ModifyItemList(updateTrainer.Pokeballs, "4", (0-self.masterballs))
		trainerservice.TryAddToPokedex(updateTrainer, self.pkmndata, self.pokemon.IsShiny)
		trainerservice.UpsertTrainer(updateTrainer)
		return await self.message.edit(view=self, embed=None, content=f'Obtained one **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)}** for **${self.price}**{" and **20 Masterballs**" if self.pkmndata.Rarity >= 8 else ""}')

	def PokemonDesc(self):
		mark = Dexmark if ((self.pkmndata.PokedexId in self.trainer.Formdex) if not self.pokemon.IsShiny else (self.pkmndata.Id in self.trainer.Shinydex)) else ''
		pkmnData = t2a(body=[['Rarity:', f'{self.pkmndata.Rarity}', '|', 'Height:', self.pkmndata.Height/10],
                         ['Color:',f'{self.pkmndata.Color}', '|','Weight:', self.pkmndata.Weight/10], 
                         ['Capture:',f'{self.pkmndata.CaptureRate}/255', '|','Female:', f'{self.pkmndata.FemaleChance}/8' if self.pkmndata.FemaleChance >= 0 else 'N/A'], 
                         ['Types:', f'{"/".join(self.pkmndata.Types)}', Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0) if self.pkmndata.PokedexId in self.trainer.Pokedex else ''
		return f'{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} {mark}\n{f"```{pkmnData}```" if pkmnData else ""}'