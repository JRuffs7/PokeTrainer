import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import Dexmark, PokemonColor
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import commandlockservice, pokemonservice, trainerservice
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
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
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
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content='Left the PokeShop.', embed=None, view=None)

	@discord.ui.button(style=discord.ButtonStyle.green ,label='Confirm')
	@defer
	async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):		
		self.trainer.OwnedPokemon.append(self.pokemon)
		self.trainer.Money -= self.price
		trainerservice.ModifyItemList(self.trainer.Pokeballs, "4", (0-self.masterballs))
		trainerservice.TryAddToPokedex(self.trainer, self.pkmndata, self.pokemon.IsShiny)
		trainerservice.UpsertTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await self.message.edit(content=f'Obtained one **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)}** for **${self.price}**{" and **20 Masterballs**" if self.pkmndata.Rarity >= 8 else ""}', embed=None, view=None)

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