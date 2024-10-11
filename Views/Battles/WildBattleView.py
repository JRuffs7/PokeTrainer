import discord
from globals import BattleColor, SuccessColor
from Views.Battles.CpuBattleView import CpuBattleView
from middleware.decorators import defer
from models.Battle import BattleAction
from models.Pokemon import Pokemon, PokemonData
from models.Trainer import Trainer
from services import commandlockservice, itemservice, pokemonservice, trainerservice
from services.utility import discordservice


class WildBattleView(CpuBattleView):

	def __init__(self, trainer: Trainer, pokemon: Pokemon, ditto: bool):
		self.pokemon = pokemon
		self.data = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		self.ditto = ditto
		super(WildBattleView, self).__init__(trainer, pokemonservice.GetPokemonDisplayName(self.pokemon, self.data), [pokemon], True, ditto)

	async def on_timeout(self):
		trainerservice.UpsertTrainer(self.trainer)
		if self.ditto:
			message = f"**{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)}** revealed it's true form!"
			self.data = pokemonservice.GetPokemonById(132)
			self.pokemon = pokemonservice.GenerateSpawnPokemon(self.data, self.pokemon.Level, trainerservice.GetShinyOdds(self.trainer))
			message += f'\n**{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})** ran away!'
		else:
			message = f'**{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})** ran away!'
		embed = discordservice.CreateEmbed(
				'Ran Away', 
				message, 
				BattleColor,
				thumbnail=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		await self.message.edit(embed=embed, view=None)
		return await super().on_timeout()
	
	@defer
	async def next_button(self, inter: discord.Interaction):
		commandlockservice.DeleteLock(inter.guild.id, inter.user.id)
		self.clear_items()
		await self.message.delete(delay=0.1)
		ephemeral = False
		if self.victory == None and self.userturn.Action == BattleAction.Pokeball:
			#Sinnoh Reward
			self.candy = itemservice.TryGetCandy(trainerservice.HasRegionReward(4))
			if self.candy:
				candyStr = f'\nFound one **{self.candy.Name}**!'
				trainerservice.ModifyItemList(self.trainer, str(self.candy.Id), 1)
				trainerservice.UpsertTrainer(self.trainer)
			else:
				candyStr = ''
			if self.ditto:
				caughtMsg = f"**{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)}** revealed it's true form!"
				self.data = pokemonservice.GetPokemonById(132)
				self.pokemon = pokemonservice.GenerateSpawnPokemon(self.data, self.pokemon.Level, trainerservice.GetShinyOdds(self.trainer))
				caughtMsg += f'\n<@{inter.user.id}> used a {self.userturn.ItemUsed.Name} and captured a wild **Ditto (Lvl. {self.pokemon.Level})**!{candyStr}'
			else:
				caughtMsg = f'<@{inter.user.id}> used a {self.userturn.ItemUsed.Name} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**!{candyStr}'
			#Hoenn Reward
			expMsg = f'\n\nYour entire team also gained some XP!' if trainerservice.HasRegionReward(self.trainer, 3) else ''
			embed = discordservice.CreateEmbed(
				'Caught', 
				f'{caughtMsg}{expMsg}', 
				SuccessColor,
				thumbnail=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		elif self.victory == None and self.userturn.Action == BattleAction.Flee:
			embed = discordservice.CreateEmbed(
				'Ran Away', 
				f'<@{inter.user.id}> ran away from **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**.', 
				BattleColor,
				thumbnail=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		elif self.victory:
			candyStr = f'\nFound one **{self.candy.Name}**!' if self.candy else ''
			rewardStr = f'<@{inter.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**! Gained **$25**{candyStr}'
			embed = discordservice.CreateEmbed('Victory', rewardStr, BattleColor, thumbnail=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		else:
			embed = discordservice.CreateEmbed(
				'Defeat', 
				f'<@{inter.user.id}> was defeated by **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**.\nRan to the PokeCenter and paid $500 to revive your party.', 
				BattleColor,
				thumbnail=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		return await inter.followup.send(embed=embed, view=self, ephemeral=ephemeral)
	
	def CheckFainting(self, pokemon: Pokemon, data: PokemonData):
		if pokemon.CurrentHP == 0:
			if pokemon.Id == self.battle.TeamAPkmn.Id:
				team = self.trainerteam
				for exp in self.exppokemon:
					self.exppokemon[exp] = []
			else:
				team = []

			if not [t for t in team if t.CurrentHP > 0]:
				self.victory = pokemon.Id == self.battle.TeamBPkmn.Id
				if not self.victory:
					pokemonservice.PokeCenter(self.trainer, team)
				else:
					self.trainer.Money += 25
					#Sinnoh Reward
					self.candy = itemservice.TryGetCandy(trainerservice.HasRegionReward(4))
					if self.candy:
						trainerservice.ModifyItemList(self.trainer, str(self.candy.Id), 1)
					for expPkmn in self.exppokemon[pokemon.Id]:
						pkmn = next(p for p in self.trainerteam if p.Id == expPkmn)
						pkmnData = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
						#Alola Reward
						self.experience = pokemonservice.ExpForPokemon(
								pokemon, 
								data, 
								False,
								pkmn.Id != self.battle.TeamAPkmn.Id,
								self.battle.TeamAPkmn.Level) * (2 if trainerservice.HasRegionReward(self.trainer, 7) else 1)
						pokemonservice.AddExperience(
							pkmn, 
							pkmnData, 
							self.experience)
				commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
				trainerservice.UpsertTrainer(self.trainer)

				if not self.victory:
					self.battle.TeamAPkmn.CurrentHP = 0

				for item in self.children:
					self.remove_item(item)
				nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
				nxtbtn.callback = self.next_button
				self.add_item(nxtbtn)
			return True
		return False