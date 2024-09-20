import logging

import discord
from globals import BattleColor
from Views.Battles.CpuBattleView import CpuBattleView
from middleware.decorators import defer
from models.Cpu import CpuTrainer
from models.Pokemon import Pokemon, PokemonData
from models.Trainer import Trainer
from services import commandlockservice, itemservice, pokemonservice, trainerservice
from services.utility import discordservice


class NPCBattleView(CpuBattleView):

	def __init__(self, trainer: Trainer, npc: CpuTrainer):
		self.battleLog = logging.getLogger('battle')
		self.npc = npc
		super(NPCBattleView, self).__init__(trainer, self.npc.Name, self.npc.Team, False)

	async def on_timeout(self):
		await self.message.edit(content=f'Battle with {self.npc.Name} canceled. No exp given and all stats reset.', embed=None, view=None)
		return await super().on_timeout()
	
	@defer
	async def next_button(self, inter: discord.Interaction):
		commandlockservice.DeleteLock(inter.guild.id, inter.user.id)
		self.clear_items()
		await self.message.delete(delay=0.1)
		ephemeral = False
		if self.victory:
			itemReward = itemservice.GetItem(self.npc.Reward[0])
			rewardStr = f'<@{inter.user.id}> defeated **Trainer {self.npc.Name}** and won {f"{itemReward.Name} x{self.npc.Reward[1]}"}!'
			embed = discordservice.CreateEmbed('Victory', rewardStr, BattleColor)
			embed.set_thumbnail(url=self.npc.Sprite)
		else:
			embed = discordservice.CreateEmbed('Defeat', f'<@{inter.user.id}> was defeated by **Trainer {self.npc.Name}**.\nRan to the PokeCenter and paid $500 to revive your party.', BattleColor)
		return await inter.followup.send(embed=embed, view=self, ephemeral=ephemeral)
	
	def CheckFainting(self, pokemon: Pokemon, data: PokemonData):
		if pokemon.CurrentHP == 0:
			if pokemon.Id == self.battle.TeamAPkmn.Id:
				team = self.trainerteam
				for exp in self.exppokemon:
					self.exppokemon[exp] = [e for e in self.exppokemon[exp] if e != pokemon.Id]
			else:
				team = self.oppteam
				for expPkmn in self.exppokemon[pokemon.Id]:
					pkmn = next(p for p in self.trainerteam if p.Id == expPkmn)
					pkmnData = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
					pkmnOut = pkmn.Id == self.battle.TeamAPkmn.Id
					self.experience = pokemonservice.ExpForPokemon(
							pokemon, 
							data, 
							not pkmnOut,
							self.battle.TeamAPkmn.Level)
					pokemonservice.AddExperience(
						pkmn, 
						pkmnData, 
						self.experience)

			if not [t for t in team if t.CurrentHP > 0]:
				self.victory = pokemon.Id == self.battle.TeamBPkmn.Id
				if not self.victory:
					pokemonservice.PokeCenter(self.trainer, team)
				else:
					trainerservice.ModifyItemList(self.trainer, str(self.npc.Reward[0]), self.npc.Reward[1])
				trainerservice.UpsertTrainer(self.trainer)

				if not self.victory:
					self.battle.TeamAPkmn.CurrentHP = 0

				for item in self.children:
					self.remove_item(item)
				nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
				nxtbtn.callback = self.next_button
				self.add_item(nxtbtn)
			elif pokemon.Id == self.battle.TeamAPkmn.Id:
				self.battle.TeamAPkmn = next(p for p in team if p.CurrentHP > 0)
				self.exppokemon[self.battle.TeamBPkmn.Id].append(self.battle.TeamAPkmn.Id)
			else:
				self.battle.TeamBPkmn = next(p for p in team if p.CurrentHP > 0)
				if self.battle.TeamAPkmn.CurrentHP > 0:
					self.exppokemon[self.battle.TeamBPkmn.Id] = [self.battle.TeamAPkmn.Id]
			return True
		return False