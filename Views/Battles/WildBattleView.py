import logging

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

	def __init__(self, trainer: Trainer, pokemon: Pokemon):
		self.battleLog = logging.getLogger('battle')
		self.pokemon = pokemon
		self.data = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		super(WildBattleView, self).__init__(trainer, pokemonservice.GetPokemonDisplayName(self.pokemon, self.data), [pokemon], True)

	async def on_timeout(self):
		trainerservice.UpsertTrainer(self.trainer)
		await self.message.edit(content=f'{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level}) ran away!', embed=None, view=None)
		return await super().on_timeout()
	
	@defer
	async def next_button(self, inter: discord.Interaction):
		commandlockservice.DeleteLock(inter.guild.id, inter.user.id)
		self.clear_items()
		await self.message.delete(delay=0.1)
		ephemeral = False
		if self.victory == None and self.userturn.Action == BattleAction.Pokeball:
			caughtMsg = f'<@{inter.user.id}> used a {self.userturn.ItemUsed.Name} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**!'
			expMsg = f'\nYour entire team also gained some XP!' if trainerservice.HasRegionReward(self.trainer, 9) else ''
			embed = discordservice.CreateEmbed(
				'Caught', 
				f'{caughtMsg}{expMsg}', 
				SuccessColor)
		elif self.victory == None and self.userturn.Action == BattleAction.Flee:
			embed = discordservice.CreateEmbed(
				'Ran Away', 
				f'<@{inter.user.id}> ran away from **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**.', 
				BattleColor)
		elif self.victory:
			candyStr = f'\nFound one **{self.candy.Name}**!' if self.candy else ''
			rewardStr = f'<@{inter.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**! Gained **$25**{candyStr}'
			embed = discordservice.CreateEmbed('Victory', rewardStr, BattleColor)
		else:
			embed = discordservice.CreateEmbed('Defeat', f'<@{inter.user.id}> was defeated by **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.data)} (Lvl. {self.pokemon.Level})**.\nRan to the PokeCenter and paid $500 to revive your party.', BattleColor)
		embed.set_thumbnail(url=pokemonservice.GetPokemonImage(self.pokemon, self.data))
		return await inter.followup.send(embed=embed, view=self, ephemeral=ephemeral)
	
	def CheckFainting(self, pokemon: Pokemon, data: PokemonData):
		if pokemon.CurrentHP == 0:
			battleOver = False
			
			if pokemon.Id == self.battle.TeamAPkmn.Id:
				if not [t for t in self.trainerteam if t.CurrentHP > 0]:
					battleOver = True
					self.victory = False
					pokemonservice.PokeCenter(self.trainer, self.trainerteam)
					trainerservice.UpsertTrainer(self.trainer)
					self.battle.TeamAPkmn.CurrentHP = 0
					for item in self.children:
						self.remove_item(item)
					nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
					nxtbtn.callback = self.next_button
					self.add_item(nxtbtn)
				else:
					for exp in self.exppokemon:
						self.exppokemon[exp] = [e for e in self.exppokemon[exp] if e != pokemon.Id]
					self.battle.TeamAPkmn = next(p for p in self.trainerteam if p.CurrentHP > 0)
					self.exppokemon[self.battle.TeamBPkmn.Id].append(self.battle.TeamAPkmn.Id)
			else:
				battleOver = True
				self.victory = True
				self.candy = itemservice.TryGetCandy(trainerservice.HasRegionReward(self.trainer, 1))
				for expPkmn in self.exppokemon[pokemon.Id]:
					pkmn = next(p for p in self.trainerteam if p.Id == expPkmn)
					pkmnData = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
					self.experience = pokemonservice.ExpForPokemon(
							pokemon, 
							data, 
							True,
							pkmn.Id != self.battle.TeamAPkmn.Id,
							self.battle.TeamAPkmn.Level)
					pokemonservice.AddExperience(
						pkmn, 
						pkmnData, 
						self.experience)
				trainerservice.UpsertTrainer(self.trainer)
			
			if battleOver:
				for item in self.children:
					self.remove_item(item)
				nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
				nxtbtn.callback = self.next_button
				self.add_item(nxtbtn)
			return True
		return False