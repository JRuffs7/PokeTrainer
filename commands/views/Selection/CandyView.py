import discord
from commands.views.Selection.selectors.GenericSelector import AmountSelector
from commands.views.Selection.selectors.ItemSelector import ItemSelector
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from middleware.decorators import button_check

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

	@button_check
	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		await inter.response.defer()
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.pokemonchoice = choices[0]
		self.candychoice = None
		self.amountchoice = None
		self.ownlist = OwnedSelector(self.pokemon, 1, choices[0])
		self.candyselector = ItemSelector([itemservice.GetCandy(int(c)) for c in self.trainer.Candies if self.trainer.Candies[c] > 0])
		self.add_item(self.ownlist)
		self.add_item(self.candyselector)
		await self.message.edit(view=self)

	@button_check
	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.candychoice = int(choice)
		self.amountchoice = None
		self.ownlist = OwnedSelector(self.pokemon, 1, self.pokemonchoice)
		self.candyselector = ItemSelector([itemservice.GetCandy(int(c)) for c in self.trainer.Candies if self.trainer.Candies[c] > 0], choice)
		self.amountselector = AmountSelector(self.trainer.Candies[choice])
		self.add_item(self.ownlist)
		self.add_item(self.candyselector)
		self.add_item(self.amountselector)
		await self.message.edit(view=self)

	@button_check
	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		self.amountchoice = int(choice)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		self.clear_items()
		await self.message.edit(content='Did not give any candies.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		if self.pokemonchoice and self.candychoice and self.amountchoice:
			#Rare Candy
			pkmn = next(p for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)
			pkmnData = pokemonservice.GetPokemonById(pkmn.Pokemon_Id)
			if itemservice.GetCandy(self.candychoice).Experience == None:
				num = 0
				while num < self.amountchoice:
					pokemonservice.AddExperience(
						pkmn, 
						pkmnData, 
						(pokemonservice.NeededExperience(pkmn.Level, pkmnData.Rarity, len(pkmnData.EvolvesInto) > 0) - pkmn.CurrentExp))
					num += 1
				message = f"{pokemonservice.GetPokemonDisplayName(pkmn)} gained {self.amountchoice} level(s)."
			else:
				pokemonservice.AddExperience(
					pkmn, 
					pkmnData, 
					itemservice.GetCandy(self.candychoice).Experience*self.amountchoice)
				message = f"{pokemonservice.GetPokemonDisplayName(pkmn)} gained {itemservice.GetCandy(self.candychoice).Experience*self.amountchoice} experience points."
			trainerservice.ModifyItemList(self.trainer.Candies, str(self.candychoice), (0-self.amountchoice))
			trainerservice.UpsertTrainer(self.trainer)
			self.clear_items()
			await self.message.edit(content=message, view=self)


	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
