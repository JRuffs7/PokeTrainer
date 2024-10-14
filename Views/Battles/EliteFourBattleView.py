import discord
from globals import BattleColor, region_name
from Views.Battles.CpuBattleView import CpuBattleView
from middleware.decorators import defer
from models.Cpu import CpuTrainer
from models.Pokemon import Pokemon, PokemonData
from models.Trainer import Trainer
from services import commandlockservice, pokemonservice, trainerservice
from services.utility import discordservice


class EliteFourBattleView(CpuBattleView):

	def __init__(self, trainer: Trainer, leader: CpuTrainer):
		self.leader = leader
		super(EliteFourBattleView, self).__init__(trainer, self.leader.Name, self.leader.Team, False)
		self.clear_items()
		if trainer.CurrentEliteFour:
			cancelbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
			cancelbtn.callback = self.cancel_button
			startbtn = discord.ui.Button(label="Start", style=discord.ButtonStyle.success)
			startbtn.callback = self.start_button
			self.add_item(cancelbtn)
			self.add_item(startbtn)
		else:
			declinebtn = discord.ui.Button(label="Decline", style=discord.ButtonStyle.danger)
			declinebtn.callback = self.decline_button
			acceptbtn = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
			acceptbtn.callback = self.accept_button
			self.add_item(declinebtn)
			self.add_item(acceptbtn)

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		if self.victory is None:
			await self.message.edit(content=f'Battle with Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name} canceled. No exp given and all stats reset.', embed=None, view=None)
		elif not self.victory:
			await self.message.edit(content=f'You were defeated by Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}.\nRan to the PokeCenter and revived your party.', embed=None, view=None)
		else:
			await self.message.edit(content=f'You defeated **Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}**!\nWon ${self.leader.Reward[1]}!', embed=None, view=None)
		return await super().on_timeout()
	
	@defer
	async def decline_button(self, inter: discord.Interaction):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		self.stop()
		await self.message.delete(delay=0.1)

	@defer
	async def accept_button(self, inter: discord.Interaction):
		commandlockservice.AddEliteFourLock(self.trainer.ServerId, self.trainer.UserId)
		self.clear_items()
		cancelbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
		cancelbtn.callback = self.cancel_button
		startbtn = discord.ui.Button(label="Start", style=discord.ButtonStyle.success)
		startbtn.callback = self.start_button
		self.add_item(cancelbtn)
		self.add_item(startbtn)
		embed = discordservice.CreateEmbed(
			'Elite Four Challenge!',
			f'You are challenging Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}!',
			BattleColor
		)
		embed.set_image(url=self.leader.Sprite)
		await self.message.edit(embeds=[embed], view=self)
	
	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()

	@defer
	async def start_button(self, inter: discord.Interaction):
		self.clear_items()
		self.AddMainButtons()
		await self.send(None)
	
	@defer
	async def next_button(self, inter: discord.Interaction):
		self.clear_items()
		await self.message.delete(delay=0.1)
		ephemeral = False
		if self.victory:
			rewardStr = f'<@{inter.user.id}> defeated **Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}**!\nWon ${int(self.leader.Reward[1]/2)}!'
			if self.leader.Generation in self.trainer.EliteFour:
				rewardStr += f'\n\nCongratulations! You are now the Champion of the {region_name(self.leader.Generation)} region!'
			elif (self.leader.Id + 1)%5 != 0:
				rewardStr += f'\n\nTo challenge the next Elite Four Member, use the **/elitefour** command again. Reminder, some commands are locked until you leave the challenge.'
			else:
				rewardStr += f'\n\nTo challenge the Elite Four Champion, use the **/elitefour** command again. Reminder, some commands are locked until you leave the challenge.'
			embed = discordservice.CreateEmbed('Victory', rewardStr, BattleColor, thumbnail=self.leader.Sprite)
		else:
			embed = discordservice.CreateEmbed('Defeat', f'<@{inter.user.id}> was defeated by **Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}**.\nRan to the PokeCenter and revived your party.', BattleColor)
		return await inter.followup.send(embed=embed, view=self, ephemeral=ephemeral)
	
	def CheckFainting(self, pokemon: Pokemon, data: PokemonData):
		if pokemon.CurrentHP == 0:
			if pokemon.Id == self.battle.TeamAPkmn.Id:
				team = self.trainerteam
				for exp in self.exppokemon:
					if exp == self.battle.TeamBPkmn.Id:
						self.exppokemon[exp] = []
					else:
						self.exppokemon[exp] = [e for e in self.exppokemon[exp] if e != pokemon.Id]
			else:
				team = self.oppteam
				for expPkmn in self.exppokemon[pokemon.Id]:
					pkmn = next(p for p in self.trainerteam if p.Id == expPkmn)
					pkmnData = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
					self.experience = pokemonservice.ExpForPokemon(
							pokemon, 
							data, 
							False,
							pkmn.Id != self.battle.TeamAPkmn.Id,
							self.battle.TeamAPkmn.Level)
					if self.leader.BadgeId in self.trainer.Badges:
						self.experience = int(self.experience/2)
					pokemonservice.AddExperience(
						pkmn, 
						pkmnData, 
						self.experience)

			if not [t for t in team if t.CurrentHP > 0]:
				self.victory = pokemon.Id == self.battle.TeamBPkmn.Id
				if not self.victory:
					self.trainer.CurrentEliteFour = []
					pokemonservice.PokeCenter(team)
					commandlockservice.DeleteEliteFourLock(self.trainer.ServerId, self.trainer.UserId)
				else:
					self.trainer.Money += self.leader.Reward[1]
					if self.leader.Id%5 == 0:
						self.trainer.EliteFour.append(self.leader.Generation)
						self.trainer.CurrentEliteFour = []
						commandlockservice.DeleteEliteFourLock(self.trainer.ServerId, self.trainer.UserId)
					else:
						self.trainer.CurrentEliteFour.append(self.leader.Id)
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
	
	async def start(self, inter: discord.Interaction):
		if not self.trainer.CurrentEliteFour:
			msg = f'Starting an Elite Four Challenge will lock certain commands until the challenge is completed. The commands will unlock again once you fail or defeat all members of this Elite Four.\n\nDo you wish to continue?'
		else:
			msg = f'You are challenging Elite Four {"Member" if self.leader.Id%5 != 0 else "Champion"} {self.leader.Name}!'
		embed = discordservice.CreateEmbed(
			'Elite Four Challenge!',
			msg,
			BattleColor
		)
		if self.trainer.CurrentEliteFour:
			embed.set_image(url=self.leader.Sprite)
		await inter.followup.send(embeds=[embed], view=self, ephemeral=True)
		self.message = await inter.original_response()