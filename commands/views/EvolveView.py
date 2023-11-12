import discord

from typing import List

from services import trainerservice, pokemonservice
from models.Pokemon import PokedexEntry, Pokemon
from models.Trainer import Trainer
from commands.views.selectors.OwnedSelector import OwnedSelector
from commands.views.selectors.EvolveSelector import EvolveSelector


class EvolveView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, evolveList: List[PokedexEntry]):
		self.interaction = interaction
		self.trainer = trainer
		self.evolvelist = evolveList
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(evolveList, 1)
		self.add_item(self.ownlist)
		self.evlist = EvolveSelector([Pokemon({'Id':0,'Name':'N/A'})])
		self.add_item(self.evlist)

	async def EvolveSelection(self, inter: discord.Interaction, choice):
		self.evolvechoice = choice[0]
		await inter.response.defer()

	async def PokemonSelection(self, inter: discord.Interaction, choice):
		self.pokemonchoice = next((p for p in self.trainer.OwnedPokemon if p.Id == choice[0]), None)
		if self.pokemonchoice:
			self.evolvechoice = None
			self.remove_item(self.ownlist)
			self.remove_item(self.evlist)
			self.ownlist = OwnedSelector(self.evolvelist, 1, choice[0])
			print("own")
			self.evlist = EvolveSelector([pokemonservice.GetPokemonById(p) for p in pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon.Pokemon_Id).EvolvesInto])
			print("ev")
			self.add_item(self.ownlist)
			self.add_item(self.evlist)
			await self.message.edit(view=self)
		await inter.response.defer()


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await self.message.delete()
		await inter.response.send_message(content='Canceled evolution.',ephemeral=True)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		try:
			print(self.pokemonchoice)
			print(self.evolvechoice)
			if self.pokemonchoice and self.evolvechoice and self.evolvechoice != '0':
				evolvedPokemon = trainerservice.Evolve(self.trainer, self.pokemonchoice, int(self.evolvechoice))
				await self.message.delete()
				await inter.response.send_message(content=f"{self.pokemonchoice.GetNameString()} evolved into {evolvedPokemon.GetNameString()}",ephemeral=True)
			await inter.response.defer()
		except Exception as e:
			print(f"{e}")


	async def send(self):
		await self.interaction.response.send_message(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
