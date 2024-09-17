import logging
import math
from random import choice
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from Views.Battles.BattleTools import ItemSelector, MoveSelector, PokemonSelector
from globals import Dexmark, Formmark, PokemonColor
from middleware.decorators import defer
from models.Battle import BattleAction, CpuBattle
from models.Gym import GymLeader
from models.Item import Pokeball
from models.Pokemon import Pokemon, PokemonData
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import battleservice, commandlockservice, gymservice, itemservice, moveservice, pokemonservice, serverservice, statservice, trainerservice
from services.utility import battleai, discordservice

class CpuBattleView(discord.ui.View):

	def __init__(self, trainer: Trainer, leader: GymLeader, wildBattle: bool, isEvent: bool):
		self.battleLog = logging.getLogger('battle')
		self.trainer = trainer
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.leader = leader
		self.fleeattempts = 0
		self.usermessage: list[str] = []
		self.cpumessage: list[str] = []
		self.userailmentmessage: list[str] = []
		self.cpuailmentmessage: list[str] = []
		self.exppokemon: dict[str,list[str]] = {}
		self.victory = None
		self.candy = None
		moveIds: list[int] = []
		pokeIds: list[int] = []
		for p in self.trainerteam + leader.Team:
			moveIds.extend([m.MoveId for m in p.LearnedMoves if m.MoveId not in moveIds])
			if p.Pokemon_Id not in pokeIds:
				pokeIds.append(p.Pokemon_Id)
		self.battle = CpuBattle.from_dict({
			'IsEvent': isEvent,
			'IsWild': wildBattle,
			'TeamAPkmn': self.trainerteam[0],
			'TeamBPkmn': leader.Team[0],
			'AllPkmnData': pokemonservice.GetPokemonByIdList(pokeIds),
			'AllMoveData': moveservice.GetMovesById(moveIds),
		})
		self.usermessage: list[str] = [f'You sent out {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id), False, False)}!']
		if not wildBattle:
			self.cpumessage: list[str] = [f'{leader.Name} sent out {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}!'] 
		self.exppokemon: dict[str,list[str]] = {}
		for cpu in leader.Team:
			self.exppokemon[cpu.Id] = [self.battle.TeamAPkmn.Id] if cpu.Id == self.battle.TeamBPkmn.Id else []
		battleservice.ResetStats(self.battle, True)
		battleservice.ResetStats(self.battle, False)
		super().__init__(timeout=300)
		self.AddMainButtons()

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		if self.battle.IsWild:
			msg = f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))} (Lvl. {self.battle.TeamBPkmn.Level}) ran away!'
			trainerservice.UpsertTrainer(self.trainer)
		else:
			msg = f'Battle with {self.leader.Name} canceled. No exp given and all stats reset.'
		await self.message.edit(content=f'{msg}', embed=None, view=None)
		return await super().on_timeout()
	
	def AddMainButtons(self):
		for item in self.children:
			self.remove_item(item)

		moveChoice,self.useraction = battleservice.CanChooseAttack(self.battle, True)
		numAvailablePokemon = [p for p in self.trainerteam if p.CurrentHP > 0 and p.Id != self.battle.TeamAPkmn.Id]
		attackbtn = discord.ui.Button(label="Attack", style=discord.ButtonStyle.primary)
		attackbtn.callback = self.attack_button
		pkmnbtn = discord.ui.Button(label="Pokemon", style=discord.ButtonStyle.secondary, disabled=((not moveChoice) or len(numAvailablePokemon) < 1))
		pkmnbtn.callback = self.pokemon_button
		itembtn = discord.ui.Button(label="Items", style=discord.ButtonStyle.success, disabled=(not moveChoice))
		itembtn.callback = self.item_button
		runbtn = discord.ui.Button(label="Run", style=discord.ButtonStyle.danger, disabled=((not self.battle.IsWild) or (not moveChoice)))
		runbtn.callback = self.run_button
		self.add_item(attackbtn)
		self.add_item(pkmnbtn)
		self.add_item(itembtn)
		self.add_item(runbtn)

	@defer
	async def back_button(self, inter: discord.Interaction):
		self.AddMainButtons()
		await self.message.edit(view=self)

	@defer
	async def next_button(self, inter: discord.Interaction):
		commandlockservice.DeleteLock(inter.guild.id, inter.user.id)
		self.clear_items()
		await self.message.delete(delay=0.1)
		ephemeral = False
		if self.useraction == BattleAction.Pokeball:
			caughtMsg = f'<@{inter.user.id}> used a {self.userturn.ItemUsed.Name} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))} (Lvl. {self.battle.TeamBPkmn.Level})**!'
			expMsg = f'\nYour entire team also gained some XP!' if trainerservice.HasRegionReward(self.trainer, 9) else ''
			embed = discordservice.CreateEmbed(
				'Caught', 
				f'{caughtMsg}{expMsg}', 
				PokemonColor)
			embed.set_thumbnail(url=pokemonservice.GetPokemonImage(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)))
		elif self.useraction == BattleAction.Flee:
			embed = discordservice.CreateEmbed(
				'Ran Away', 
				f'<@{inter.user.id}> ran away from **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}.**', 
				PokemonColor)
			embed.set_thumbnail(url=pokemonservice.GetPokemonImage(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)))
		elif self.victory:
			name = f'**{self.leader.Name} (Lvl. {self.battle.TeamBPkmn.Level})**' if self.battle.IsWild else f'**{self.leader.Name}**'
			if self.battle.IsWild:
				candyStr = f'\nFound a **{self.candy.Name}**!' if self.candy else ''
				rewardStr = f'<@{inter.user.id}> defeated a wild {name}! Gained **$25**{candyStr}'
				thumbnail = pokemonservice.GetPokemonImage(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))
			elif self.battle.IsEvent:
				ephemeral = True
				server = serverservice.GetServer(inter.guild_id)
				itemReward = itemservice.GetItem(self.leader.Reward[0])
				rewardStr = f'<@{inter.user.id}> defeated {name} and won {f"${self.leader.Reward[1]}" if self.leader.Reward[0] == 0 else f"{itemReward.Name} x{self.leader.Reward[1]}"}!' 
				if server and server.CurrentEvent and server.CurrentEvent.ThreadId:
					thread = inter.guild.get_thread(server.CurrentEvent.ThreadId)
					if not thread.archived:
						await thread.send(content=rewardStr)
					else:
						ephemeral = False
				else:
					ephemeral = False
				thumbnail = self.leader.Sprite
			else:
				rewardStr = f'<@{inter.user.id}> defeated {name} and obtained the {gymservice.GetBadgeById(self.leader.BadgeId).Name} Badge!\nWon ${self.leader.Reward[1]}!'
				thumbnail = gymservice.GetBadgeById(self.leader.BadgeId).Sprite
			embed = discordservice.CreateEmbed('Victory', rewardStr, PokemonColor)
			embed.set_thumbnail(url=thumbnail)
		else:
			name = f'**{self.leader.Name} (Lvl. {self.battle.TeamBPkmn.Level})**' if self.battle.IsWild else f'**{self.leader.Name}**'
			embed = discordservice.CreateEmbed('Defeat', f'<@{inter.user.id}> was defeated by {name}.\nRan to the PokeCenter and paid $500 to revive your party.', PokemonColor)
		return await inter.followup.send(embed=embed, view=self, ephemeral=ephemeral)

	#region Attack

	@defer
	async def attack_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)

		canChoose,self.useraction = battleservice.CanChooseAttack(self.battle, True)
		if canChoose:
			if [m for m in self.battle.TeamAPkmn.LearnedMoves if m.PP > 0]:
				self.add_item(MoveSelector([m for m in self.battle.TeamAPkmn.LearnedMoves if m.PP > 0]))
				backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
				backBtn.callback = self.back_button
				self.add_item(backBtn)
				await self.message.edit(view=self)
			else:
				await self.MoveSelection(inter, '165')
		else:
			lastTurn = battleservice.GetTurn(self.battle, True, 1, self.battle.TeamAPkmn.Id)
			await self.MoveSelection(inter, str(lastTurn.Move.Id) if lastTurn.Move else '165')

	async def MoveSelection(self, inter: discord.Interaction, choice: str): 
		self.userturn = battleservice.CreateTurn(self.battle.CurrentTurn, True, self.battle.TeamAPkmn.Id, self.useraction, moveservice.GetMoveById(int(choice)))
		await self.TakeTurn(inter)

	#endregion

	#region Pokemon

	@defer
	async def pokemon_button(self, inter: discord.Interaction):
		self.useraction = BattleAction.Swap
		for item in self.children:
			self.remove_item(item)
		self.add_item(PokemonSelector([p for p in self.trainerteam if p.CurrentHP > 0 and p.Id != self.battle.TeamAPkmn.Id], self.battle.AllPkmnData))
		backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
		backBtn.callback = self.back_button
		self.add_item(backBtn)
		await self.message.edit(view=self)
	
	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		pkmn = choice if self.useraction == BattleAction.Swap else self.battle.TeamAPkmn.Id
		self.userturn = battleservice.CreateTurn(self.battle.CurrentTurn, True, pkmn, self.useraction, 
			item=self.itemchoice if self.useraction == BattleAction.Item else None,
			itemUse=choice if self.useraction == BattleAction.Item else None)
		await self.TakeTurn(inter)

	#endregion

	#region Items

	@defer
	async def item_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
			
		ballBtn = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.primary, custom_id='pokeball', disabled=(not self.battle.IsWild or not itemservice.GetTrainerPokeballs(self.trainer)))
		ballBtn.callback = self.item_cat_button
		potionBtn = discord.ui.Button(label="Potions", style=discord.ButtonStyle.green, custom_id='potion', disabled=(not itemservice.GetTrainerPotions(self.trainer)))
		potionBtn.callback = self.item_cat_button
		backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
		backBtn.callback = self.back_button
		self.add_item(ballBtn)
		self.add_item(potionBtn)
		self.add_item(backBtn)
		await self.message.edit(view=self)
	
	@defer
	async def item_cat_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'pokeball':
			self.useraction = BattleAction.Pokeball
			itemList = itemservice.GetTrainerPokeballs(self.trainer)
		else:
			self.useraction = BattleAction.Item
			itemList = itemservice.GetTrainerPotions(self.trainer)
		for item in self.children:
			self.remove_item(item)
		self.add_item(ItemSelector(self.trainer.Items, itemList))
		backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
		backBtn.callback = self.back_button
		self.add_item(backBtn)
		await self.message.edit(view=self)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		for item in self.children:
			self.remove_item(item)
		if self.useraction == BattleAction.Pokeball:
			self.userturn = battleservice.CreateTurn(self.battle.CurrentTurn, True, self.battle.TeamAPkmn.Id, self.useraction, 
				item=itemservice.GetPokeball(int(choice)))
			await self.TakeTurn(inter)
		elif self.useraction == BattleAction.Item:
			self.itemchoice = itemservice.GetPotion(int(choice))
			available = []
			for p in self.trainerteam:
				if self.itemchoice.HealingAmount and p.CurrentHP < statservice.GenerateStat(p, next(po for po in self.battle.AllPkmnData if po.Id == p.Pokemon_Id), StatEnum.HP):
					available.append(p)
				elif p.CurrentAilment in self.itemchoice.AilmentCures:
					available.append(p)
			if not available:
				await self.message.edit(content=f'No Pokemon available to use this item on. Try again.')
				await self.item_button(None)
			else:
				self.add_item(PokemonSelector(available, self.battle.AllPkmnData))
				backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
				backBtn.callback = self.back_button
				self.add_item(backBtn)
				await self.message.edit(view=self)

	#endregion

	#region Run

	@defer
	async def run_button(self, inter: discord.Interaction):
		self.fleeattempts += 1
		self.userturn = battleservice.CreateTurn(self.battle.CurrentTurn,True,self.battle.TeamAPkmn.Id,BattleAction.Flee)
		await self.TakeTurn(inter)

	#endregion

	#region Move

	async def TakeTurn(self, inter: discord.Interaction):
		self.usermessage = []
		self.cpumessage = []
		self.userailmentmessage = []
		self.cpuailmentmessage = []
		teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		teamBData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
		self.cputurn = battleai.CreateCpuTurn(self.battle, self.leader.Team)
		if self.userturn.Action == BattleAction.Flee:
			self.battle.Turns.insert(0, self.userturn)
			if self.fleeattempts == 3 or battleservice.FleeAttempt(self.battle, self.fleeattempts):
				trainerservice.UpsertTrainer(self.trainer)
				return await self.next_button(inter)
			self.usermessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} failed to run away!')

		if self.userturn.Action == BattleAction.Pokeball:
			if type(self.userturn.ItemUsed) is not Pokeball:
				self.usermessage.append('Error with turn. Skipping...')
				self.cpumessage.append('Error with turn. Skipping...')
				self.AddMainButtons()
				await self.message.edit(embeds=self.GetEmbeds(), view=self)
			self.battle.Turns.insert(0, self.userturn)
			if battleservice.TryCapture(self.userturn.ItemUsed, self.trainer, self.battle):
				trainerservice.UpsertTrainer(self.trainer)
				return await self.next_button(inter)
			self.usermessage.append(f'Tried to capture using a **{self.userturn.ItemUsed.Name}**...it broke free!')

		if self.userturn.Action == BattleAction.Swap:
			battleservice.ResetStats(self.battle, True)
			teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
			self.exppokemon[self.battle.TeamBPkmn.Id].append(self.userturn.PokemonId)
			self.battle.TeamAPkmn = next(p for p in self.trainerteam if p.Id == self.userturn.PokemonId)
			self.battle.Turns.insert(0, self.userturn)
			self.usermessage.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)}!')
		if self.cputurn.Action == BattleAction.Swap:
			battleservice.ResetStats(self.battle, False)
			teamBData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
			self.exppokemon[self.battle.TeamBPkmn.Id] = [self.battle.TeamAPkmn.Id]
			self.battle.TeamBPkmn = next(p for p in self.leader.Team if p.Id == self.cputurn.PokemonId)
			self.battle.Turns.insert(0, self.cputurn)
			self.cpumessage.append(f'{self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)}!')

		if self.userturn.Action == BattleAction.Item:
			pkmn = next(p for p in self.trainerteam if p.Id == self.userturn.ItemUsedOnId)
			data = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
			pokemonservice.UseItem(pkmn, data, self.userturn.ItemUsed)
			self.battle.Turns.insert(0, self.userturn)
			self.usermessage.append(f'You used a **{self.userturn.ItemUsed.Name.upper()}** on {pokemonservice.GetPokemonDisplayName(pkmn, data, False, False)}!')
		if self.cputurn.Action == BattleAction.Item:
			pkmn = next(p for p in self.leader.Team if p.Id == self.cputurn.ItemUsedOnId)
			data = next(p for p in self.battle.AllPkmnData if p.Id == pkmn.Pokemon_Id)
			pokemonservice.UseItem(pkmn, data, self.cputurn.ItemUsed)
			self.battle.Turns.insert(0, self.cputurn)
			self.usermessage.append(f'You used a **{self.cputurn.ItemUsed.Name.upper()}** on {pokemonservice.GetPokemonDisplayName(pkmn, data, False, False)}!')
		
		if battleservice.TeamAAttackFirst(self.userturn.Move, self.cputurn.Move, self.battle):
			if self.userturn.Move:
				self.userturn.DamageDone = await self.Attack(self.battle.TeamAPkmn, self.battle.TeamBPkmn, True)
				self.battle.Turns.insert(0, self.userturn)
			if self.cputurn.Move and self.battle.TeamAPkmn.CurrentHP > 0 and self.battle.TeamBPkmn.CurrentHP > 0:
				self.cputurn.DamageDone = await self.Attack(self.battle.TeamBPkmn, self.battle.TeamAPkmn, False)
				self.battle.Turns.insert(0, self.cputurn)
		else:
			if self.cputurn.Move:
				self.cputurn.DamageDone = await self.Attack(self.battle.TeamBPkmn, self.battle.TeamAPkmn, False)
				self.battle.Turns.insert(0, self.cputurn)
			if self.userturn.Move and self.battle.TeamAPkmn.CurrentHP > 0 and self.battle.TeamBPkmn.CurrentHP > 0:
				self.userturn.DamageDone = await self.Attack(self.battle.TeamAPkmn, self.battle.TeamBPkmn, True)
				self.battle.Turns.insert(0, self.userturn)
		self.battle.CurrentTurn += 1
		self.AddMainButtons()
		self.TakePostTurn()
		await self.message.edit(embeds=self.GetEmbeds(), view=self)

	def TakePostTurn(self):
		teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		teamBData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
		shouldReturn = False
		if self.CheckFainting(self.battle.TeamAPkmn, teamAData):
			self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} fainted!')
			if self.victory is None:
				teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
				self.userailmentmessage.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id), False, False)}!')
			shouldReturn = True
		if self.CheckFainting(self.battle.TeamBPkmn, teamBData):
			self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} fainted!')
			if self.battle.TeamAPkmn.CurrentHP > 0:
				self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} gained {self.experience} XP!')
			if len(self.exppokemon[self.battle.TeamBPkmn.Id]) > 1:
				self.cpuailmentmessage.append(f'Other participants gained shared XP!')
			if self.victory is None:
				self.cpuailmentmessage.append(f'{self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}!')
			shouldReturn = True
		if shouldReturn:
			return

		ailDmg = battleservice.AilmentDamage(self.battle.TeamAPkmn, teamAData, self.battle.TeamBPkmn, teamBData)
		match self.battle.TeamAPkmn.CurrentAilment:
			case 4: #Burn
				self.userailmentmessage.append(f"{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} lost **{ailDmg}** to **BURN**.")
			case 5: #Poison
				self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} lost **{ailDmg}** to **POISON**.')
			case 8: #Trap
				self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} lost **{ailDmg}** to **{moveservice.GetMoveById(self.battle.TeamATrapId).Name}**.')
			case 18: #Leech
				self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} lost **{ailDmg} to **Leech Seed**.')
				self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} is healed **{ailDmg} by **Leech Seed**.')
		if self.CheckFainting(self.battle.TeamAPkmn, teamAData):
			self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} fainted!')
			if self.victory is None:
				self.userailmentmessage.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id), False, False)}!')
			return
		
		ailDmg = battleservice.AilmentDamage(self.battle.TeamBPkmn, teamBData, self.battle.TeamAPkmn, teamAData)
		match self.battle.TeamBPkmn.CurrentAilment:
			case 4: #Burn
				self.cpuailmentmessage.append(f"{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} lost **{ailDmg}** to **BURN**.")
			case 5: #Poison
				self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} lost **{ailDmg}** to **POISON**.')
			case 8: #Trap
				self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} lost **{ailDmg}** to **{moveservice.GetMoveById(self.battle.TeamBTrapId).Name}**.')
			case 18: #Leech
				self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} lost **{ailDmg}** to **Leech Seed**.')
				self.userailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} is healed **{ailDmg} by **Leech Seed**.')
		if self.CheckFainting(self.battle.TeamBPkmn, teamBData):
			self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} fainted!')
			self.cpuailmentmessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} gained {self.experience} XP!')
			if len(self.exppokemon[self.battle.TeamBPkmn.Id]) > 1:
				self.cpuailmentmessage.append(f'Other participants gained XP as well!')
			if self.victory is None:
				self.userailmentmessage.append(f'{self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}!')
			return

	#endregion

	#region Other

	async def Attack(self, attack: Pokemon, defend: Pokemon, teamA: bool):
		if teamA:
			turn = self.userturn
			oppTurn = self.cputurn
			messages = self.usermessage
			firstAttack = next((t for t in self.battle.Turns if t.TurnNum == self.battle.CurrentTurn and t.PokemonId == self.battle.TeamBPkmn and t.Move),None) == None
			self.battle.TeamATrap = max(self.battle.TeamATrap - 1, 0)
			self.battle.TeamAConfusion = max(self.battle.TeamATrap - 1, 0)
			self.battle.TeamASpecReduce = max(self.battle.TeamASpecReduce - 1, 0)
			self.battle.TeamAPhysReduce = max(self.battle.TeamAPhysReduce - 1, 0)
		else:
			turn = self.cputurn
			oppTurn = self.userturn
			messages = self.cpumessage
			firstAttack = next((t for t in self.battle.Turns if t.TurnNum == self.battle.CurrentTurn and t.PokemonId == self.battle.TeamAPkmn and t.Move),None) == None
			self.battle.TeamBTrap = max(self.battle.TeamBTrap - 1, 0)
			self.battle.TeamBConfusion = max(self.battle.TeamBTrap - 1, 0)
			self.battle.TeamBSpecReduce = max(self.battle.TeamBSpecReduce - 1, 0)
			self.battle.TeamBPhysReduce = max(self.battle.TeamBPhysReduce - 1, 0)
		attackData = next(p for p in self.battle.AllPkmnData if p.Id == attack.Pokemon_Id)
		defendData = next(p for p in self.battle.AllPkmnData if p.Id == defend.Pokemon_Id)
		pkmnName = pokemonservice.GetPokemonDisplayName(attack, attackData, False, False)

		if turn.Action == BattleAction.Charge:
			messages.append(f'{pkmnName} used **{turn.Move.Name}**!')
			messages.append("It's charging up...")
			if turn.Move.ChargeImmune:
				self.battle.TeamAImmune = teamA
				self.battle.TeamBImmune = not teamA
			return None
		if turn.Action == BattleAction.Recharge:
			messages.append(f'{pkmnName} has to recharge!')
			return None

		#Check ailments:
		ailmentCheck = battleservice.AilmentCheck(turn.Action, attack, self.battle)
		if ailmentCheck == False:
			if teamA:
				self.battle.TeamAConsAttacks = 0
			else:
				self.battle.TeamBConsAttacks = 0
			turn.Action = BattleAction.Paralyzed if attack.CurrentAilment == 1 else BattleAction.Sleep if attack.CurrentAilment == 2 else BattleAction.Frozen if attack.CurrentAilment == 3 else BattleAction.Confused
			messages.append(statservice.GetAilmentFailMessage(pkmnName, attack.CurrentAilment))
			if turn.Action == BattleAction.Confused:
				battleservice.ConfusionDamage(attack, attackData)
			return None
		elif ailmentCheck == True:
			messages.append(statservice.GetRecoveryMessage(attack, attackData, self.battle.TeamATrapId if teamA else self.battle.TeamBTrapId))
			attack.CurrentAilment = None	
			self.battle.TeamATrapId = None if teamA else self.battle.TeamATrapId	
			self.battle.TeamBTrapId = None if not teamA else self.battle.TeamBTrapId	

		messages.append(statservice.GetAilmentMessage(pkmnName, attack.CurrentAilment))
		messages.append(f'{pkmnName} used **{turn.Move.Name}**!')
		#Check Fails/Charges

		if next(m for m in attack.LearnedMoves if m.MoveId == turn.Move.Id).PP == 0:
			messages.append(f'No PP left for {turn.Move.Name}')
			return None

		turn.Action = battleservice.SpecialHitCases(turn.Move, self.battle, attack, defend, firstAttack, oppTurn.Move)
		if turn.Action == BattleAction.Charge:
			messages.append("It's charging up...")
			if turn.Move.ChargeImmune:
				self.battle.TeamAImmune = teamA
				self.battle.TeamBImmune = not teamA
			return None
		
		next(m for m in attack.LearnedMoves if m.MoveId == turn.Move.Id).PP -= 1
		self.battle.TeamAImmune = False if teamA else self.battle.TeamAImmune
		self.battle.TeamBImmune = False if not teamA else self.battle.TeamBImmune

		if turn.Action == BattleAction.Failed:
			messages.append('It failed!')
			return None
		
		if not battleservice.MoveAccuracy(turn.Move, self.battle, teamA):
			turn.Action = BattleAction.Missed
			messages.append('It missed!')
			slfDmg = battleservice.SelfDamage(turn.Move, attack, attackData)
			if slfDmg > 0:
				messages.append(f'{pkmnName} took **{slfDmg}** recoil damage!')
				if attack.CurrentHP == 0:
					team = self.trainerteam if teamA else self.leader.Team
					if teamA and [t for t in team if t.CurrentHP > 0]:
						messages.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id), False, False)}!')
					elif not teamA and [t for t in team if t.CurrentHP > 0]:
						messages.append(f'{self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}!')
			return None
		
		# ATTACK THEM
		turn.Action == BattleAction.Attack
		isConfused = battleservice.ConsecutiveAttack(turn.Move, self.battle, teamA)
		numattacks = choice(range(turn.Move.MinAttacks,turn.Move.MaxAttacks+1))
		damage = 0
		for _ in range(numattacks):
			dmg,crit = battleservice.AttackDamage(turn.Move, attack, defend, self.battle)
			if crit:
				messages.append('Critical Hit!')
			damage += dmg
		if turn.Move.AttackType != 'status':
			messages.append(moveservice.GetEffectiveString(turn.Move.MoveType, defendData.Types, damage))
		if numattacks > 1:
			messages.append(f'It hit {numattacks} times!')

		if isConfused:
			attack.CurrentAilment = 6
			messages.append(statservice.GetAilmentGainedMessage(attack, attackData, None))

		healStr = battleservice.MoveDrain(turn.Move, attack, attackData, damage)
		if healStr:
			messages.append(healStr)
			if attack.CurrentHP == 0:
				team = self.trainerteam if teamA else self.leader.Team
				if teamA and [t for t in team if t.CurrentHP > 0]:
					messages.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id), False, False)}!')
				elif not teamA and [t for t in team if t.CurrentHP > 0]:
					messages.append(f'{self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}!')

		ailStr = battleservice.ApplyAilment(self.battle, turn.Move, defend, defendData)
		if ailStr:
			messages.append(ailStr)

		statStr = battleservice.ApplyStatChange(turn.Move, self.battle, teamA)
		if statStr:
			messages.extend(statStr)

		if turn.Move.Id == 113:
			if teamA:
				self.battle.TeamASpecReduce = 5
			else:
				self.battle.TeamBSpecReduce = 5
			messages.append('Special attacks will now deal less damage!')

		if turn.Move.Id == 115:
			if teamA:
				self.battle.TeamAPhysReduce = 5
			else:
				self.battle.TeamBPhysReduce = 5
			messages.append('Physical attacks will now deal less damage!')

		if turn.Move.Id == 283:
			defend.CurrentHP -= math.ceil(damage)
			attack.CurrentHP += math.floor(damage)
		
		if turn.Move.Id == 694:
			if teamA:
				self.battle.TeamASpecReduce = 5
				self.battle.TeamAPhysReduce = 5
			else:
				self.battle.TeamBSpecReduce = 5
				self.battle.TeamBPhysReduce = 5
			messages.append('Special/Physical attacks will now deal less damage!')

		if turn.Move.Id == 740:
			for t in self.trainerteam:
				if t.CurrentAilment in [1,2,3,4,5]:
					t.CurrentAilment = None
			messages.append('Cured all allies of status conditions!')

		return damage

	def CheckFainting(self, pokemon: Pokemon, data: PokemonData):
		if pokemon.CurrentHP == 0:
			if pokemon.Id == self.battle.TeamAPkmn.Id:
				team = self.trainerteam
				for exp in self.exppokemon:
					self.exppokemon[exp] = [e for e in self.exppokemon[exp] if e != pokemon.Id]
			else:
				team = self.leader.Team
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
					self.candy = trainerservice.FightWin(self.trainer)
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

	def Description(self):
		usrMsg = '\n'.join([s for s in self.usermessage if s])
		cpuMsg = '\n'.join([s for s in self.cpumessage if s])
		usrAMsg = '\n'.join([s for s in self.userailmentmessage if s])
		cpuAMsg = '\n'.join([s for s in self.cpuailmentmessage if s])

		trainerPkData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		cpuPkData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
		descArray = [
				[f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, trainerPkData, False, False)}', '|', f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, cpuPkData, False, False)}'],
				[f'Lvl. {self.battle.TeamAPkmn.Level}', '|', f'Lvl. {self.battle.TeamBPkmn.Level}'],
				[f'HP: {self.battle.TeamAPkmn.CurrentHP}/{statservice.GenerateStat(self.battle.TeamAPkmn, trainerPkData, StatEnum.HP)}', '|', f'HP: {self.battle.TeamBPkmn.CurrentHP}/{statservice.GenerateStat(self.battle.TeamBPkmn, cpuPkData, StatEnum.HP)}']
		]
		if self.battle.TeamAPkmn.CurrentAilment or self.battle.TeamBPkmn.CurrentAilment:
			descArray.append([f'{statservice.GetAilment(self.battle.TeamAPkmn.CurrentAilment).Name.upper()}' if self.battle.TeamAPkmn.CurrentAilment else '', '|', f'{statservice.GetAilment(self.battle.TeamBPkmn.CurrentAilment).Name.upper()}' if self.battle.TeamBPkmn.CurrentAilment else ''])
		pkmnData = t2a(
			body=descArray, 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.CENTER,Alignment.RIGHT],
			style=PresetStyle.plain,
			cell_padding=0)
		moveSeparator = '\n--------------------\n'
		userfirst = next((t for t in self.battle.Turns), None) != None and next(t for t in self.battle.Turns).PokemonId == self.battle.TeamBPkmn.Id
		moveArrays = [usrMsg,cpuMsg,usrAMsg,cpuAMsg] if userfirst else [cpuMsg,usrMsg,usrAMsg,cpuAMsg]
		moveStr = moveSeparator.join([st for st in moveArrays if st])
		if self.battle.IsWild:
			hasDexmark = Dexmark if ((cpuPkData.PokedexId in self.trainer.Pokedex) if not self.battle.TeamBPkmn.IsShiny else (cpuPkData.Id in self.trainer.Shinydex)) else ''
			hasFormmark = Formmark if ((cpuPkData.Id in self.trainer.Formdex) if not self.battle.TeamBPkmn.IsShiny else False) else ''
			newL = '\n'
			titleStr = f'__**A Wild {self.leader.Name} appeared!**__{f"{newL}{hasDexmark}{hasFormmark}" if hasDexmark or hasFormmark else ""}'
		else:
			titleStr = f'__**{self.leader.Name} wants to Battle!**__'
		return f'{titleStr}\n{moveStr}```{pkmnData}```'

	def GetEmbeds(self):
		embed = discordservice.CreateEmbed('',self.Description(),PokemonColor,'https://pokeapi.co')
		embed.set_image(url='https://imgur.com/sW1ByMV.png')
		embed2 = discordservice.CreateEmbed('','',PokemonColor,'https://pokeapi.co')
		embed2.set_image(url=pokemonservice.GetPokemonImage(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)))
		embed3 = discordservice.CreateEmbed('','',PokemonColor,'https://pokeapi.co')
		embed3.set_image(url=pokemonservice.GetPokemonImage(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)))
		embed4 = discordservice.CreateEmbed('','',PokemonColor,'https://pokeapi.co')
		embed4.set_image(url='https://imgur.com/sW1ByMV.png')
		return [embed,embed2,embed3,embed4]

	#endregion

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(embeds=self.GetEmbeds(), view=self, ephemeral=True)
		self.message = await inter.original_response()
