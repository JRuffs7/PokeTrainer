import discord

from Views.Selectors import MoveSelector, PokemonSelector, ItemSelector
from middleware.decorators import defer
from models.Trainer import Trainer
from services import commandlockservice, itemservice, moveservice, pokemonservice, trainerservice

class UsePotionView(discord.ui.View):

	def __init__(self, trainer: Trainer):
		self.trainer = trainer
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.pkmndata = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in self.trainerteam])
		self.pkmnchoice = None
		self.itemchoice = None
		self.movechoice = None
		super().__init__(timeout=300)
		self.AddSelectors()

	def AddSelectors(self):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)
		self.pkmnchoice = None
		self.pkmnchoicedata = None
		self.itemchoice = None
		self.movechoice = None
		self.add_item(ItemSelector(self.trainer.Items, itemservice.GetTrainerPotions(self.trainer)))
		self.add_item(PokemonSelector([p for p in self.trainerteam], descType=2))

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete(delay=0.1)
		return await super().on_timeout()
	
	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		self.pkmnchoice = next(t for t in self.trainerteam if t.Id == choice)
		self.pkmnchoicedata = next(p for p in self.pkmndata if p.Id == self.pkmnchoice.Pokemon_Id)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		self.itemchoice = itemservice.GetPotion(int(choice))

	async def MoveSelection(self, inter: discord.Interaction, choice: str):
		self.movechoice = moveservice.GetMoveById(int(choice))

	@discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
	@defer
	async def exit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await self.on_timeout()

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		message = None
		if self.pkmnchoice and self.itemchoice:
			if self.itemchoice.PPAmount and not self.itemchoice.PPAll and not self.movechoice:
				for item in self.children:
					if type(item) is not discord.ui.Button:
						self.remove_item(item)
				self.add_item(MoveSelector(self.pkmnchoice.LearnedMoves))
				return await self.message.edit(content=message, view=self)
			
			if pokemonservice.TryUsePotion(self.pkmnchoice, self.pkmnchoicedata, self.itemchoice, self.movechoice):
				trainerservice.ModifyItemList(self.trainer, str(self.itemchoice.Id), -1)
				trainerservice.UpsertTrainer(self.trainer)
				message = f'Used a **{self.itemchoice.Name}** on {pokemonservice.GetPokemonDisplayName(self.pkmnchoice, self.pkmnchoicedata)}.'
			elif (self.itemchoice.PPAmount) and (not self.itemchoice.PPAll) and (not self.movechoice):
				message = f'Must select a move to use a **{self.itemchoice.Name}**.'
			elif (self.itemchoice.PPAmount) and (not self.itemchoice.PPAll) and (self.movechoice):
				message = f'This move is already at full PP.'
			else:
				message = f'Cannot use **{self.itemchoice.Name}** on {pokemonservice.GetPokemonDisplayName(self.pkmnchoice, self.pkmnchoicedata)}.'
		self.AddSelectors()
		await self.message.edit(content=message, view=self)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
