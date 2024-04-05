from datetime import UTC, datetime
import discord

from globals import DateFormat, TrainerColor
from models.Pokemon import Pokemon, PokemonData
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from services.utility import discordservice


class DaycareView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = [next(p for p in trainer.OwnedPokemon if p.Id == d) for d in trainer.Daycare]
		self.pkmndata = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in self.pokemon])
		self.currentPage = 0
		super().__init__(timeout=300)
		if len(trainer.Daycare) > 1:
			self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
			self.prevBtn.callback = self.page_button
			self.add_item(self.prevBtn)
		remBtn = discord.ui.Button(label="Remove", style=discord.ButtonStyle.green)
		remBtn.callback = self.remove_button
		self.add_item(remBtn)
		if len(trainer.Daycare) > 1:
			self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
			self.nextBtn.callback = self.page_button
			self.add_item(self.nextBtn)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		pkmn = self.pokemon[self.currentPage]
		data = next(p for p in self.pkmndata if p.Id == pkmn.Pokemon_Id)
		embed = discordservice.CreateEmbed(
				f'{self.interaction.user.display_name}s Daycare',
				self.Description(pkmn, data),
				TrainerColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(pkmn, data))
		embed.set_footer(text=f'{self.currentPage+1}/{len(self.trainer.Daycare)}')
		await self.message.edit(embed=embed, view=self)

	async def page_button(self, interaction: discord.Interaction):
		await interaction.response.defer()
		if interaction.data['custom_id'] == 'prev':
			self.currentPage = 0
		else:
			self.currentPage = 1
		self.prevBtn.disabled = self.currentPage == 0
		self.nextBtn.disabled = self.currentPage == 1
		await self.update_message()

	async def remove_button(self, interaction: discord.Interaction):
		await interaction.response.defer()
		await self.message.delete(delay=0.01)
		pkmn = self.pokemon[self.currentPage]
		data = next(p for p in self.pkmndata if p.Id == pkmn.Pokemon_Id)
		timeAdded = datetime.strptime(self.trainer.Daycare.pop(pkmn.Id), DateFormat).replace(tzinfo=UTC)
		hoursSpent = int((datetime.now(UTC) - timeAdded).total_seconds()//3600)
		pokemonservice.AddExperience(pkmn, data, 10*hoursSpent)
		trainerservice.UpsertTrainer(self.trainer)
		await interaction.followup.send(content=f'{pokemonservice.GetPokemonDisplayName(pkmn, data)} has been removed from the daycare and is now Level {pkmn.Level}!', ephemeral=True)



	def Description(self, pokemon: Pokemon, pkmnData: PokemonData):
		timeAdded = datetime.strptime(self.trainer.Daycare[pokemon.Id], DateFormat).replace(tzinfo=UTC)
		hoursSpent = int((datetime.now(UTC) - timeAdded).total_seconds()//3600)
		levelsGained = pokemonservice.SimulateLevelGain(pokemon.Level, pokemon.CurrentExp, pkmnData.Rarity, len(pkmnData.EvolvesInto)>0, 10*hoursSpent)
		return f'**__{pokemonservice.GetPokemonDisplayName(pokemon, pkmnData)}__**\n\nLevel: {pokemon.Level} -> {(pokemon.Level + levelsGained)}'