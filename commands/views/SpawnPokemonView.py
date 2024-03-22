import asyncio
import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import Checkmark, FightReaction, GreatBallReaction, PokeballReaction, PokemonColor, UltraBallReaction, WarningSign
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from services.utility import discordservice

class SpawnPokemonView(discord.ui.View):

	def __init__(
			self, interaction: discord.Interaction, trainer: Trainer, pokemon: Pokemon):
		self.battleLog = logging.getLogger('battle')	
		self.captureLog = logging.getLogger('capture')	
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		super().__init__(timeout=60)
		self.teamslotview = OwnedSelector(trainerservice.GetTeam(trainer), 1, trainer.Team[0])
		self.add_item(self.teamslotview)

	async def send(self):
		if not self.pokemon:
			return await self.interaction.followup.send("Failed to spawn a Pokemon. Please try again.", ephemeral=True)
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		embed = discordservice.CreateEmbed(
				self.GetTitle(),
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(self.pokemon))
		embed.set_footer(text='Set Your Battle Pokemon Below')
		await self.message.edit(content=f'Current Trainer HP: {self.TrainerHealthString(self.trainer)}', embed=embed, view=self)

	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		await inter.response.defer()
		trainerservice.SetTeamSlot(self.trainer, 0, choice[0])

	@discord.ui.button(label=PokeballReaction)
	async def pokeball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Pokeball")

	@discord.ui.button(label=GreatBallReaction)
	async def greatball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Greatball")

	@discord.ui.button(label=UltraBallReaction)
	async def ultraball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Ultraball")

	@discord.ui.button(label=FightReaction, custom_id="fight")
	async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		updatedTrainer = trainerservice.GetTrainer(self.interaction.guild_id, self.interaction.user.id)
		trainerPkmn = next(p for p in updatedTrainer.OwnedPokemon if p.Id == updatedTrainer.Team[0])
		fight = trainerservice.TryWildFight(updatedTrainer, self.pokemon)
		if fight is None:
			return await self.message.edit(content=f"You do not have any health! Restore with **/usepotion**. You can buy potions from the **/shop**", view=self)
		
		healthLost = fight[0]
		candy = fight[1]
		if healthLost >= 10 or updatedTrainer.Health == 0:
			self.battleLog.info(f'{interaction.user.display_name} was defeated by a wild {self.pkmndata.Name}')
			await self.message.delete()
			return await interaction.followup.send(content=f'<@{self.interaction.user.id}> and {pokemonservice.GetPokemonDisplayName(trainerPkmn)} were defeated by a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)} (Lvl. {self.pokemon.Level})** and lost {healthLost}hp.\nNo experience or money gained.')
		else:
			self.battleLog.info(f'{interaction.user.display_name} defeated a wild {self.pkmndata.Name}')
			await self.message.delete()
			battleMsg = f'<@{self.interaction.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)} (Lvl. {self.pokemon.Level})**!'
			expMsg = f'{pokemonservice.GetPokemonDisplayName(trainerPkmn)} gained {self.pkmndata.Rarity*self.pokemon.Level*2 if self.pkmndata.Rarity <= 2 else self.pkmndata.Rarity*self.pokemon.Level}xp'
			expShareMsg = f'The rest of your team gained half exp. as well.' if trainerservice.HasRegionReward(updatedTrainer, 1) else ''
			rewardMsg = f'Trainer lost {healthLost}hp and gained $50.{f" Found one **{candy.Name}**!" if candy else ""}'
			newline = '\n'
			return await interaction.followup.send(content=f'{newline.join([battleMsg, expMsg, expShareMsg, rewardMsg])}')
			
			
	async def TryCapture(self, interaction: discord.Interaction, label: str, ball: str):
		await interaction.response.defer()
		updatedTrainer = trainerservice.GetTrainer(self.interaction.guild_id, self.interaction.user.id)
		pokeballId = '1' if label == PokeballReaction else '2' if label == GreatBallReaction else '3' if label == UltraBallReaction else '4'
		if updatedTrainer.Pokeballs[str(pokeballId)] <= 0:
			await self.message.edit(content=f"You do not have any {ball}s. Buy some from the **/shop**, try another ball, or fight!\nCurrent Trainer HP: {self.TrainerHealthString(updatedTrainer)}", view=self)
		elif trainerservice.TryCapture(label, updatedTrainer, self.pokemon):
			self.captureLog.info(f'{interaction.guild.name} - {self.interaction.user.display_name} used {ball} and caught a {self.pkmndata.Name}')
			await self.message.delete()
			await interaction.followup.send(content=f'<@{self.interaction.user.id}> used a {ball} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})**!\nAlso gained $25')
		else:
			await self.message.edit(content=f"Capture failed! Try again or fight.\nCurrent Trainer HP: {self.TrainerHealthString(updatedTrainer)}", view=self)

	def GetTitle(self):
		return f'{f"{Checkmark} " if self.pkmndata.PokedexId in self.trainer.Pokedex else ""}{pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})'

	def TrainerHealthString(self, trainer: Trainer):
		return f"{trainer.Health}{WarningSign}" if trainer.Health < 10 else f"{trainer.Health}"

	def PokemonDesc(self):
		pkmnData = t2a(
			body=[
				['Rarity:', f"{self.pkmndata.Rarity}", '|', 'Height:', self.pokemon.Height],
				['Color:',f"{self.pkmndata.Color}", '|','Weight:', self.pokemon.Weight], 
				['Types:', f"{self.pkmndata.Types[0]}"f"{'/' + self.pkmndata.Types[1] if len(self.pkmndata.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"```{pkmnData}```"
