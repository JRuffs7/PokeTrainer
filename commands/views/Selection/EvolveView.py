from random import choice
import discord
from middleware.decorators import defer

from services import itemservice, trainerservice, pokemonservice
from models.Pokemon import Pokemon, PokemonData
from models.Trainer import Trainer
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from commands.views.Selection.selectors.EvolveSelector import EvolveSelector


class EvolveView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, evolveMon: list[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.evolveMon = evolveMon
		self.pkmnChoiceData = None
		self.evolvechoice = None
		self.randomidlist = None
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(evolveMon, 1)
		self.add_item(self.ownlist)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def EvolveSelection(self, inter: discord.Interaction, evchoice: str):
		evId = choice(self.randomidlist) if evchoice == "-1" else int(evchoice)
		self.evolvechoice = next(p for p in self.pkmnChoiceData.EvolvesInto if evId == p.EvolveID)

	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.pokemonchoice = next(p for p in self.trainer.OwnedPokemon if p.Id == choice[0])
		self.pkmnChoiceData = pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon_Id)
		self.evolvechoice = None
		self.ownlist = OwnedSelector(self.evolveMon, 1, choice[0])
		availableList = pokemonservice.GetPokemonByIdList(pokemonservice.AvailableEvolutions(self.pokemonchoice, self.pkmnChoiceData, trainerservice.GetTrainerItemList(self.trainer, 3)))
		if self.pkmnChoiceData.RandomEvolve and len(availableList) > 1:
			self.randomidlist = pokemonservice.GetRandomEvolveList(self.pkmnChoiceData, [a.Id for a in availableList])
			if self.randomidlist:
				availableList = [a for a in availableList if a.Id not in self.randomidlist]
				availableList.insert(0, PokemonData({'Id': -1, 'Name': 'Random Evolution', 'EvolvesInto': []}))
		evolveListData = []
		for a in availableList:
			desc: str
			if a.Id == -1:
				randPkmn = pokemonservice.GetPokemonByIdList(self.randomidlist) if len(self.randomidlist) < 5 else []
				desc = " | ".join([r.Name for r in randPkmn]) if randPkmn else 'Evolve into a random evolution in this line.'
			else:
				descArr: list[str] = []
				evolutionData = next(p for p in self.pkmnChoiceData.EvolvesInto if p.EvolveID == a.Id)
				if evolutionData.EvolveLevel:
					descArr.append(f'Level {evolutionData.EvolveLevel}')
				if evolutionData.GenderNeeded:
					descArr.append('Female' if evolutionData.GenderNeeded == 1 else 'Male')
				if evolutionData.ItemNeeded:
					descArr.append(itemservice.GetItem(evolutionData.ItemNeeded).Name)
				desc = f'Reqs: {" | ".join(descArr)}'
			evolveListData.append({'Pokemon': a, 'Description': desc})
		self.evlist = EvolveSelector(evolveListData)
		self.add_item(self.ownlist)
		self.add_item(self.evlist)
		await self.message.edit(view=self)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='Canceled evolution.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoice and self.evolvechoice:
			evPkmn = trainerservice.Evolve(self.trainer, self.pokemonchoice, self.pkmnChoiceData, self.evolvechoice)
			self.clear_items()
			displayMon = Pokemon.from_dict({'IsFemale': evPkmn.IsFemale, 'IsShiny': evPkmn.IsShiny, 'Pokemon_Id': self.evolvechoice.EvolveID})
			await self.message.edit(content=f"**{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, self.pkmnChoiceData)}** evolved into **{pokemonservice.GetPokemonDisplayName(displayMon)}**", view=self)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
