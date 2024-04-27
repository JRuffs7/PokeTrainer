from math import ceil
import discord
from commands.views.Selection.selectors.GenericSelector import AmountSelector
from commands.views.Selection.selectors.ItemSelector import ItemSelector
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from middleware.decorators import defer

from models.Pokemon import Pokemon
from services import itemservice, pokemonservice, trainerservice
from models.Trainer import Trainer


class CandyView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, pokemon: list[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.pokemon = pokemon
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(pokemon, 1)
		self.add_item(self.ownlist)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.pokemonchoice = next(p for p in self.trainer.OwnedPokemon if p.Id == choices[0])
		self.candychoice = None
		self.amountchoice = None
		self.ownlist = OwnedSelector(self.pokemon, 1, choices[0])
		self.candyselector = ItemSelector([itemservice.GetCandy(int(c)) for c in self.trainer.Candies if self.trainer.Candies[c] > 0])
		self.add_item(self.ownlist)
		self.add_item(self.candyselector)
		await self.message.edit(view=self)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.candychoice = itemservice.GetCandy(int(choice))
		self.amountchoice = None
		self.ownlist = OwnedSelector(self.pokemon, 1, self.pokemonchoice.Id)
		self.candyselector = ItemSelector([itemservice.GetCandy(int(c)) for c in self.trainer.Candies if self.trainer.Candies[c] > 0], choice)
		self.amountselector = AmountSelector(self.trainer.Candies[choice])
		self.add_item(self.ownlist)
		self.add_item(self.candyselector)
		self.add_item(self.amountselector)
		await self.message.edit(view=self)

	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		self.amountchoice = int(choice)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='Did not give any candies.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoice and self.candychoice and self.amountchoice:
			#Rare Candy
			pkmnData = pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon_Id)
			if self.candychoice.Experience == None:
				num = 0
				while num < self.amountchoice and self.pokemonchoice.Level < 100:
					pokemonservice.AddExperience(
						self.pokemonchoice, 
						pkmnData, 
						(pokemonservice.NeededExperience(self.pokemonchoice.Level, pkmnData.Rarity, pkmnData.EvolvesInto) - self.pokemonchoice.CurrentExp))
					num += 1
				message = f"{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, pkmnData)} gained {num} level(s)."
				trainerservice.ModifyItemList(self.trainer.Candies, str(self.candychoice.Id), (0-num))
			else:
				num = 0
				while num < self.amountchoice and self.pokemonchoice.Level < 100:
					nextLevel = pokemonservice.NeededExperience(self.pokemonchoice.Level, pkmnData.Rarity, pkmnData.EvolvesInto) - self.pokemonchoice.CurrentExp
					numToUse = ceil(nextLevel/self.candychoice.Experience)
					numToUse = self.amountchoice - num if numToUse > self.amountchoice - num else numToUse
					pokemonservice.AddExperience(
						self.pokemonchoice, 
						pkmnData, 
						self.candychoice.Experience*numToUse)
					num += numToUse
				message = f"{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, pkmnData)} gained {self.candychoice.Experience*num} experience points."
				trainerservice.ModifyItemList(self.trainer.Candies, str(self.candychoice.Id), (0-num))
			trainerservice.UpsertTrainer(self.trainer)
			self.clear_items()
			await self.message.edit(content=message, view=self)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
