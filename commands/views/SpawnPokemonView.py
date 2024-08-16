import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import Dexmark, FightReaction, Formmark, GreatBallReaction, PokeballReaction, PokemonColor, UltraBallReaction, WarningSign
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice, statservice, trainerservice
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
		self.pressed = False

	async def on_timeout(self):
		await self.message.edit(content=f'{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level}) ran away!', embed=None, view=None)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		self.trainer = trainerservice.GetTrainer(self.trainer.ServerId, self.trainer.UserId)
		trainerservice.SetTeamSlot(self.trainer, 0, choice[0])

	@discord.ui.button(label=PokeballReaction)
	@defer
	async def pokeball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not self.pressed:
			self.pressed = True
			await self.TryCapture(interaction, button.label, "Pokeball")

	@discord.ui.button(label=GreatBallReaction)
	@defer
	async def greatball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not self.pressed:
			self.pressed = True
			await self.TryCapture(interaction, button.label, "Greatball")

	@discord.ui.button(label=UltraBallReaction)
	@defer
	async def ultraball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not self.pressed:
			self.pressed = True
			await self.TryCapture(interaction, button.label, "Ultraball")

	@discord.ui.button(label=FightReaction, custom_id="fight")
	@defer
	async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not self.pressed:
			self.pressed = True
			updatedTrainer = trainerservice.GetTrainer(self.interaction.guild_id, self.interaction.user.id)
			if updatedTrainer is None:
				self.pressed = False
				return await self.message.edit(content=f"Error fighting. Please try again.", view=self)
			elif updatedTrainer.Health <= 0:
				self.pressed = False
				return await self.message.edit(content=f"You do not have any health! Restore with **/usepotion**. You can buy potions from the **/shop**", view=self)
			
			trainerPkmn = next(p for p in updatedTrainer.OwnedPokemon if p.Id == updatedTrainer.Team[0])
			trainerPkmnData = pokemonservice.GetPokemonById(trainerPkmn.Pokemon_Id)

			healthLost, candy = trainerservice.TryWildFight(updatedTrainer, trainerPkmnData, self.pokemon, self.pkmndata)
			if healthLost >= 10 or updatedTrainer.Health == 0:
				self.battleLog.info(f'{interaction.user.display_name} was defeated by a wild {self.pkmndata.Name}')
				await self.message.delete(delay=0.01)
				return await interaction.followup.send(content=f'<@{self.interaction.user.id}> and {pokemonservice.GetPokemonDisplayName(trainerPkmn, trainerPkmnData)} were defeated by a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})** and lost {healthLost}hp.\nNo experience or money gained.')
			else:
				self.battleLog.info(f'{interaction.user.display_name} defeated a wild {self.pkmndata.Name}')
				await self.message.delete(delay=0.01)
				battleMsg = f'<@{self.interaction.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})**!'
				exp = self.pkmndata.Rarity*self.pokemon.Level*2 if self.pkmndata.Rarity <= 2 else self.pkmndata.Rarity*self.pokemon.Level
				expMsg = f'{pokemonservice.GetPokemonDisplayName(trainerPkmn, trainerPkmnData)} gained **{exp} XP**'
				expShareMsg = f'{pokemonservice.GetPokemonDisplayName(next(p for p in updatedTrainer.OwnedPokemon if p.Id == updatedTrainer.Team[1]))} gained **{int(exp/2)} XP** from the Exp. Share' if trainerservice.HasRegionReward(updatedTrainer, 1) and len(updatedTrainer.Team) > 1 else ''
				rewardMsg = f'Trainer lost **{healthLost}hp** and gained **$25**.{f" Found one **{candy.Name}**!" if candy else ""}'
				newline = '\n'
				return await interaction.followup.send(content=f'{newline.join([battleMsg, expMsg, expShareMsg, rewardMsg] if expShareMsg else [battleMsg, expMsg, rewardMsg])}')
			
	async def TryCapture(self, interaction: discord.Interaction, label: str, ball: str):
		self.trainer = trainerservice.GetTrainer(self.trainer.ServerId, self.trainer.UserId)
		pokeballId = '4' if label == PokeballReaction else '3' if label == GreatBallReaction else '2' if label == UltraBallReaction else '1'
		if self.trainer.Health <= 0:
				self.pressed = False
				return await self.message.edit(content=f"You do not have any health! Restore with **/usepotion**. You can buy potions from the **/shop**", view=self)
		elif self.trainer.Items[pokeballId] <= 0:
			self.pressed = False
			await self.message.edit(content=f"You do not have any {ball}s. Buy some from the **/shop**, try another ball, or fight!\nCurrent Trainer HP: {self.TrainerHealthString(self.trainer)}", view=self)
		elif trainerservice.TryCapture(pokeballId, self.trainer, self.pokemon):
			self.captureLog.info(f'{interaction.guild.name} - {self.interaction.user.display_name} used {ball} and caught a {self.pkmndata.Name}{"-SHINY" if self.pokemon.IsShiny else ""}')
			await self.message.delete(delay=0.01)
			baseMsg = f'<@{self.interaction.user.id}> used a {ball} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})**!'
			expMsg = f'\nYour entire team also gained **{self.pokemon.Level} XP**' if trainerservice.HasRegionReward(self.trainer, 9) else ''
			await interaction.followup.send(content=f'{baseMsg}{expMsg}')
		else:
			self.pressed = False
			await self.message.edit(content=f"Capture failed! Lost **{5-int(pokeballId)}hp** Try again or fight.\nCurrent Trainer HP: {self.TrainerHealthString(self.trainer)}", view=self)

	def TrainerHealthString(self, trainer: Trainer):
		return f"{trainer.Health}{WarningSign}" if trainer.Health < 10 else f"{trainer.Health}"

	def PokemonDesc(self):
		hasDexmark = Dexmark if ((self.pkmndata.PokedexId in self.trainer.Pokedex) if not self.pokemon.IsShiny else (self.pkmndata.Id in self.trainer.Shinydex)) else ''
		hasFormmark = Formmark if ((self.pkmndata.Id in self.trainer.Formdex) if not self.pokemon.IsShiny else False) else ''
		return f"Level: {self.pokemon.Level}\nDex: {f"{hasDexmark}{hasFormmark} " if hasDexmark or hasFormmark else ""}\nType(s): {'/'.join([statservice.GetType(t).Name for t in self.pkmndata.Types])}"

	async def send(self):
		if not self.pokemon:
			return await self.interaction.followup.send("Failed to spawn a Pokemon. Please try again.", ephemeral=True)
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		embed = discordservice.CreateEmbed(
				f'Wild {pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)}!',
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(self.pokemon, self.pkmndata))
		embed.set_footer(text='Choose An Action')
