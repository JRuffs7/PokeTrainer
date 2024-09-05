import logging
import math
from random import choice
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from commands.views.Battles.BattleTools import ItemSelector, MoveSelector, PokemonSelector
from globals import Dexmark, Formmark, PokemonColor, WarningSign, to_dict
from middleware.decorators import defer
from models.Battle import BattleAction, CpuBattle
from models.Gym import GymLeader
from models.Item import Pokeball, Potion
from models.Move import MoveData
from models.Pokemon import Pokemon, PokemonData
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import battleservice, gymservice, itemservice, moveservice, pokemonservice, serverservice, statservice, trainerservice
from services.utility import battleai, discordservice

class CpuBattleView(discord.ui.View):

	def __init__(self, trainer: Trainer, leader: GymLeader, wildBattle: bool, isEvent: bool):
		self.battleLog = logging.getLogger('battle')
		self.trainer = trainer
		self.leader = leader
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.fleeattempts = 0
		self.userfirst = False
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
		self.usermessage: list[str] = [f'You sent out {pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn), False, False)}!']
		if wildBattle:
			self.cpumessage: list[str] = []
		else:
			self.cpumessage: list[str] = [f'{leader.Name} sent out {pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn), False, False)}!'] 
		self.exppokemon: dict[str,list[str]] = {}
		for cpu in leader.Team:
			self.exppokemon[cpu.Id] = []

		#region DELETE AFTER
		for p in leader.Team:
			p.CurrentHP = choice(range(1,statservice.GenerateStat(p,next(po for po in self.battle.AllPkmnData if po.Id == p.Pokemon_Id), StatEnum.HP)+1))
			p.CurrentAilment = choice([1,2,3,4,5,None])
		print([f'{p.Pokemon_Id} - Lvl {p.Level} - HP: {p.CurrentHP} - {p.CurrentAilment}' for p in leader.Team])
		#endregion

		self.ResetStats(True)
		self.ResetStats(False)
		super().__init__(timeout=300)
		self.AddMainButtons()

	async def on_timeout(self):
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

		swapOnly = self.battle.TeamAPkmn.CurrentHP == 0
		moveChoice,action = battleservice.CanChooseAttack(self.battle, True) if not swapOnly else (False, None)
		attackbtn = discord.ui.Button(label="Attack", style=discord.ButtonStyle.primary, disabled=swapOnly)
		attackbtn.callback = self.attack_button
		pkmnbtn = discord.ui.Button(label="Pokemon", style=discord.ButtonStyle.secondary, disabled=((not swapOnly) and (not moveChoice or (len([p for p in self.trainerteam if p.CurrentHP > 0 and p.Id != self.battle.TeamAPkmn.Id]) < 1))))
		pkmnbtn.callback = self.pokemon_button
		itembtn = discord.ui.Button(label="Items", style=discord.ButtonStyle.success, disabled=(not moveChoice or swapOnly))
		itembtn.callback = self.item_button
		runbtn = discord.ui.Button(label="Run", style=discord.ButtonStyle.danger, disabled=((not self.battle.IsWild) or not moveChoice or swapOnly))
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
		self.clear_items()
		self.message.delete(delay=0.1)
		ephemeral = False
		if self.victory:
			name = f'**{self.leader.Name} (Lvl. {self.battle.TeamBPkmn.Level})**' if self.battle.IsWild else f'**{self.leader.Name}**'
			if self.battle.IsWild:
				rewardStr = f'<@{self.interaction.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})**!\nGained **{self.expgain} XP**'
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
			else:
				rewardStr = f'<@{inter.user.id}> defeated {name} and obtained the {gymservice.GetBadgeById(self.leader.BadgeId).Name} Badge!\nWon ${self.leader.Reward[1]}!'
			embed = discordservice.CreateEmbed('Victory', rewardStr, PokemonColor)
		else:
			embed = discordservice.CreateEmbed('Defeat', 'You have been defeated.\nRan to the PokeCenter and paid $500 to revive your party.', PokemonColor)
		return await inter.followup.send(embed=[embed], view=self, ephemeral=ephemeral)

	#region Attack

	@defer
	async def attack_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)

		canChoose,self.useraction = battleservice.CanChooseAttack(self.battle, True)
		if canChoose:
			if [m for m in self.battle.TeamAPkmn.LearnedMoves if m.PP > 0]:
				self.add_item(MoveSelector(self.battle.TeamAPkmn.LearnedMoves))
				backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
				backBtn.callback = self.back_button
				self.add_item(backBtn)
				await self.message.edit(view=self)
			else:
				await self.MoveSelection(inter, '165')
		else:
			lastTurn = next(t for t in self.battle.Turns if t.TeamA)
			self.MoveSelection(inter, str(lastTurn.Move.Id) if lastTurn.Move else '165')

	async def MoveSelection(self, inter: discord.Interaction, choice: str): 
		self.userattack = moveservice.GetMoveById(int(choice))
		await self.TakeTurn(inter.user.id)

	#endregion

	#region Pokemon

	@defer
	async def pokemon_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
		if self.battle.TeamAPkmn and [p for p in self.trainerteam if p.CurrentHP > 0]:
			self.useraction = BattleAction.Swap
			self.userfirst = True
			self.add_item(PokemonSelector([p for p in self.trainerteam if p.CurrentHP > 0 and p.Id != self.battle.TeamAPkmn.Id], self.battle.AllPkmnData))
			backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
			backBtn.callback = self.back_button
			self.add_item(backBtn)
			await self.message.edit(view=self)
		else:
			self.back_button(None)
	
	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		self.userpkmnchoice = next((p for p in self.trainerteam if p.Id == choice), None)
		if self.userpkmnchoice and (self.useraction == BattleAction.Swap or self.useritemchoice):
			await self.TakeTurn(inter.user.id)


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
		for item in self.children:
			self.remove_item(item)

		self.useritemchoice = None
		self.userfirst = True
		if inter.data['custom_id'] == 'pokeball':
			self.useraction = BattleAction.Pokeball
			itemList = itemservice.GetTrainerPokeballs(self.trainer)
		else:
			self.useraction = BattleAction.Item
			itemList = itemservice.GetTrainerPotions(self.trainer)
		self.add_item(ItemSelector(itemList))
		backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
		backBtn.callback = self.back_button
		self.add_item(backBtn)
		await self.message.edit(view=self)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		if self.useraction == BattleAction.Pokeball:
			self.useritemchoice = itemservice.GetPokeball(int(choice))
			await self.TakeTurn(inter.user.id)
		elif self.useraction == BattleAction.Item:
			self.useritemchoice = itemservice.GetPotion(int(choice))
			healPkmn = []
			ailPkmn = []
			if self.useritemchoice.HealingAmount:
				healPkmn = [po for po in [p for p in self.trainerteam if p.CurrentHP > 0] if po.CurrentHP < statservice.GenerateStat(po, next(pok for pok in self.battle.AllPkmnData if pok.Id == po.Pokemon_Id), StatEnum.HP)]
			if self.useritemchoice.AilmentCures:
				ailPkmn = [po for po in [p for p in self.trainerteam if p.CurrentHP > 0] if po.CurrentAilment in self.useritemchoice.AilmentCures]
			available = list(set(healPkmn)|set(ailPkmn))
			if not available:
				await self.message.edit(content=f'No Pokemon available to use this item on. Try again.')
				await self.item_button(None)
			else:
				self.add_item(PokemonSelector(available, self.battle.AllPkmnData))
				await self.message.edit(view=self)

	#endregion

	#region Run

	@defer
	async def run_button(self, inter: discord.Interaction):
		self.useraction = BattleAction.Flee
		self.userfirst = True
		self.fleeattempts += 1
		await self.TakeTurn(inter.user.id)

	#endregion

	#region Move

	async def TakeTurn(self, userId: int):
		self.usermessage = []
		self.cpumessage = []
		teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		teamBData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)

		cpuChoose,cpuAction = battleservice.CanChooseAttack(self.battle, False)
		if cpuChoose:
			cpuAction, cpuObj = battleai.CpuAction(self.battle, self.leader.Team)
		else:
			pTurn = next(t for t in self.battle.Turns if not t.TeamA)
			cpuObj = pTurn.Move if pTurn.Move else moveservice.GetMoveById(165)


		if self.useraction == BattleAction.Swap:
			battleservice.ResetStats(self.battle, True)
			self.userfirst = True
			self.battle.TeamAPkmn = self.userpkmnchoice
			self.usermessage.append(f'You swapped in {pokemonservice.GetPokemonDisplayName(self.userpkmnchoice, next(p for p in self.battle.AllPkmnData if p.Id == self.userpkmnchoice.Pokemon_Id), False, False)}.')
		
		elif self.useraction == BattleAction.Pokeball:
			if type(self.useritemchoice) is not Pokeball:
				self.useraction = BattleAction.Error
				self.usermessage.append('Error with turn. Skipping...')
				self.cpumessage.append('Error with turn. Skipping...')
			else:
				self.userfirst = True
				if battleservice.TryCapture(self.useritemchoice, self.trainer, self.battle):
					caughtMsg = f'<@{userId}> used a {self.useritemchoice.Name} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))} (Lvl. {self.battle.TeamBPkmn.Level})**!'
					expMsg = f'\nYour entire team also gained some XP!' if trainerservice.HasRegionReward(self.trainer, 9) else ''
					trainerservice.UpsertTrainer(self.trainer)
					await self.message.edit(content=f'{caughtMsg}{expMsg}', embeds=[], view=None)
					self.stop()
					return
				self.usermessage.append(f'Tried to capture using a **{self.useritemchoice.Name}**...it broke free!')
		
		elif self.useraction == BattleAction.Item:
			if type(self.useritemchoice) is not Potion:
				self.useraction = BattleAction.Error
				self.usermessage.append('Error with turn. Skipping...')
				self.cpumessage.append('Error with turn. Skipping...')
			else:
				self.userfirst = True
				data = next(p for p in self.battle.AllPkmnData if p.Id == self.userpkmnchoice.Pokemon_Id)
				pokemonservice.UseItem(self.userpkmnchoice, data, self.useritemchoice)
				self.usermessage.append(f'You used a **{self.useritemchoice.Name.upper()}** on {pokemonservice.GetPokemonDisplayName(self.userpkmnchoice, data, False, False)}!')
		
		elif self.useraction == BattleAction.Flee:
			self.userfirst = True
			if self.fleeattempts == 3 or battleservice.FleeAttempt(self.battle, self.fleeattempts):
				trainerservice.UpsertTrainer(self.trainer)
				await self.message.edit(content=f'<@{userId}> ran away from **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}.**', embeds=[], view=None)
				self.stop()
				return
			self.usermessage.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} failed to run away!')


		if type(cpuObj) is Pokemon:
			pData = next(p for p in self.battle.AllPkmnData if p.Id == cpuObj.Pokemon_Id)
			if cpuAction == BattleAction.Swap:
				battleservice.ResetStats(self.battle, False)
				self.battle.TeamBPkmn = cpuObj
				self.cpumessage = f'The opponent swapped in {pokemonservice.GetPokemonDisplayName(cpuObj, pData, False, False)}!'
			elif cpuAction == BattleAction.Item:
				item = itemservice.GetPotion(23) #Full Restore
				pokemonservice.UseItem(cpuObj, pData, item)
				self.cpuitempkmn = cpuObj
				self.cpumessage = f'The opponent used a **{item.Name.upper()}** on {pokemonservice.GetPokemonDisplayName(cpuObj, pData, False, False)}.'

		if type(cpuObj) is MoveData:
			self.cpuattack = cpuObj

		if self.useraction == BattleAction.Attack and cpuAction == BattleAction.Attack:
			self.userfirst = battleservice.TeamAAttackFirst(self.userattack, cpuObj, self.battle)
		userDmg = None
		cpuDmg = None
		if self.useraction == BattleAction.Attack:
			#Check ailments:
			ailmentCheck = battleservice.AilmentCheck(self.battle.TeamAPkmn)
			if ailmentCheck is not None and not ailmentCheck:
				self.useraction = BattleAction.Paralyzed if self.battle.TeamAPkmn.CurrentAilment == 1 else BattleAction.Sleep if self.battle.TeamAPkmn.CurrentAilment == 2 else BattleAction.Frozen if self.battle.TeamAPkmn.CurrentAilment == 3 else BattleAction.Confused
				if self.useraction == BattleAction.Confused:
					battleservice.ConfusionDamage(self.battle.TeamAPkmn, teamAData)
					self.usermessage.extend([f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} is confused!','It hurt itself in its confusion!'])
					if self.battle.TeamAPkmn.CurrentHP == 0:
						self.usermessage.extend(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} fainted!')

			else:
				self.recoverymsg = statservice.GetRecoveryMessage(self.battle.TeamAPkmn, teamAData)
				
				if self.userfirst:
					if self.userattack.Charge or self.userattack.ChargeImmune:
						userTurn = battleservice.AddTurn(self.battle, self.currentturn, True, self.useraction, self.userattack, )
					if self.userattack.UniqueDamage:
						return
			
			
		if self.userfirst:
			battleservice.AddTurn(self.battle, self.currentturn, True, self.useraction, self.userattack, userDmg)
			battleservice.AddTurn(self.battle, self.currentturn, False, cpuAction, cpuObj if type(cpuObj) is MoveData else None, cpuDmg)
		else:
			battleservice.AddTurn(self.battle, self.currentturn, False, cpuAction, cpuObj if type(cpuObj) is MoveData else None, cpuDmg)
			battleservice.AddTurn(self.battle, self.currentturn, True, self.useraction, self.userattack, userDmg)
		self.AddMainButtons()
		await self.message.edit(embeds=(await self.GetEmbeds()), view=self)

	async def TakePostTurn(self):
		teamAData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		teamBData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
		if self.battle.TeamAPkmn.CurrentHP == 0:
			if not [t for t in self.trainerteam if t.CurrentHP > 0]:
				self.victory = False
				for item in self.children:
					self.remove_item(item)
				nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
				nxtbtn.callback = self.run_button
				self.add_item(nxtbtn)
			return [f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, teamAData, False, False)} fainted.']
		
		if self.battle.TeamBPkmn.CurrentHP == 0:
			if not [t for t in self.trainerteam if t.CurrentHP > 0]:
				self.victory = True
				for item in self.children:
					self.remove_item(item)
				nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
				nxtbtn.callback = self.run_button
				self.add_item(nxtbtn)
			return [f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} fainted.']
		
		ailmentStrings = []
		battleservice.AilmentDamage(self.battle.TeamAPkmn, teamAData)
		match self.battle.TeamAPkmn.CurrentAilment:
			case 4: #Burn
				ailmentStrings.append(f"{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} is hurt by it's **BURN**.")
			case 5: #Poison
				ailmentStrings.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} is hurt by **POISON**.')
			case 8: #Trap
				ailmentStrings.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} is hurt by **{moveservice.GetMoveById(self.battle.TeamATrap).Name}**.')
			case 18: #Leech
				ailmentStrings.append(f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, teamBData, False, False)} is hurt by **Leech Seed**.')

	#endregion

	#region Other

	def UserAttack(self, data: PokemonData):
		self.usermessage = []
		attack = True
		pkmnName = pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, data, False, False)
		if self.battle.TeamBPkmn.CurrentHP == 0:
			attack = False
			self.useraction = BattleAction.Failed
			self.usermessage.append('Attack failed! Opponent already fainted.')
		#Check ailments:
		ailmentCheck = battleservice.AilmentCheck(self.battle.TeamAPkmn)
		if ailmentCheck is not None and not ailmentCheck and attack:
			self.useraction = BattleAction.Paralyzed if self.battle.TeamAPkmn.CurrentAilment == 1 else BattleAction.Sleep if self.battle.TeamAPkmn.CurrentAilment == 2 else BattleAction.Frozen if self.battle.TeamAPkmn.CurrentAilment == 3 else BattleAction.Confused
			self.usermessage.append(statservice.GetAilmentFailMessage(pkmnName, self.battle.TeamAPkmn.CurrentAilment))
			if self.useraction == BattleAction.Confused:
				battleservice.ConfusionDamage(self.battle.TeamAPkmn, data)
				if self.battle.TeamAPkmn.CurrentHP == 0:
					self.usermessage.append(f'{self.usermessage}\n{pkmnName} fainted!')
		elif ailmentCheck is not None and ailmentCheck:
			self.usermessage.append(statservice.GetRecoveryMessage(self.battle.TeamAPkmn, data))			

		if not attack:
			return

		self.usermessage.append(statservice.GetAilmentMessage(pkmnName, self.battle.TeamAPkmn.CurrentAilment))
		#Check Fails/Charges
		self.useraction = battleservice.SpecialHitCases(self.userattack, self.battle, self.userfirst, True, self.userattack, self.cpuattack)
		if self.useraction == BattleAction.Failed:
			self.usermessage.extend([f'{pkmnName} used **{self.userattack.Name}**!','It failed!'])
			return
		if self.useraction == BattleAction.Charge:
			self.usermessage.extend([f'{pkmnName} used **{self.userattack.Name}**!',"It's charging up..."])
			return
		

		if not battleservice.MoveAccuracy(self.userattack, self.battle, True):
			self.useraction = BattleAction.Missed
			self.usermessage.extend([f'{pkmnName} used **{self.userattack.Name}**!','It missed!'])
			return
		

		# ATTACK THEM
		damage = battleservice.AttackDamage(self.userattack, self.battle.TeamAPkmn, self.battle.TeamBPkmn, self.battle)

		if self.userattack == 283:
			self.battle.TeamBPkmn.CurrentHP += math.ceil(damage)
			self.battle.TeamAPkmn.CurrentHP += math.floor(damage)
		
		if self.userattack == 740:
			for t in self.trainerteam:
				if t.CurrentAilment in [1,2,3,4,5]:
					t.CurrentAilment = None
			self.usermessage.append('Cured all allies of status conditions!')

	def ResetStats(self, teamA: bool):
		if teamA:
			self.battle.TeamAStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
			self.battle.TeamAConsAttacks = 0
			if self.battle.TeamAPkmn.CurrentAilment in [6,8,18]:
				self.battle.TeamAPkmn.CurrentAilment = None
		else:
			self.battle.TeamBStats = {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0}
			self.battle.TeamBConsAttacks = 0
			if self.battle.TeamBPkmn.CurrentAilment in [6,8,18]:
				self.battle.TeamBPkmn.CurrentAilment = None

	def GetTurnDesc(self, teamA: bool):
		lastTurn = next((t for t in self.battle.Turns if t.TeamA == teamA), None)
		if not lastTurn:
			return f'{"You" if teamA else self.leader.Name} sent out {pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)}!'
		if lastTurn.Action == BattleAction.Item:
			pokemon = self.userpkmnchoice if teamA else self.cpuitempkmn
			opponent = self.userpkmnchoice if not teamA else self.cpuitempkmn
		else:
			pokemon = self.battle.TeamAPkmn if teamA else self.battle.TeamBPkmn
			opponent = self.battle.TeamAPkmn if not teamA else self.battle.TeamBPkmn
		data = next(p for p in self.battle.AllPkmnData if p.Id == pokemon.Pokemon_Id)
		oppData = next(p for p in self.battle.AllPkmnData if p.Id == opponent.Pokemon_Id)
		opponentCall = 'Wild ' if self.battle.IsWild else 'Enemy '
		pokemonCall = f'{"" if teamA else opponentCall}{pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)}'
		turnStr = ''
		match(lastTurn.Action):
			case BattleAction.Swap:
				turnStr = f'{"You" if teamA else self.leader.Name} swapped in {pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)}!'
			case BattleAction.Item:
				turnStr = f'{"You" if teamA else self.leader.Name} used a **{self.useritemchoice.Name.upper() if teamA else "FULL RESTORE"}** on {pokemonservice.GetPokemonDisplayName(pokemon, data, False, False)}!'
			case BattleAction.Pokeball:
				turnStr = f'Tried to capture using a **{self.useritemchoice.Name}**...it broke free!'
			case BattleAction.Flee:
				turnStr = f'{pokemonCall} failed to run away!'
			case BattleAction.Charge:
				turnStr = f'{pokemonCall} is charging up...'
			case BattleAction.Recharge:
				turnStr = f"{pokemonCall} can't move!"
			case BattleAction.Sleep:
				return f'{pokemonCall} is fast asleep!'
			case BattleAction.Frozen:
				return f'{pokemonCall} is frozen solid!'
			case BattleAction.Paralyzed:
				turnStr = f"It can't move!"
			case BattleAction.Confused:
				turnStr = f'It hurt itself in its confusion!'
			case BattleAction.Attack:
				moveUsed = self.userattack if teamA else self.cpuattack
				typeEffect = statservice.TypeDamage(moveUsed, oppData.Types)
				effectStr = '\nIt was super effective!' if typeEffect > 1 else "\nIt's not very effective." if typeEffect < 1 else "It had no effect!" if typeEffect == 0 else ''
				turnStr = f'{pokemonCall} used **{moveUsed}**!{effectStr}'
			case BattleAction.Missed:
				moveUsed = self.userattack if teamA else self.cpuattack
				turnStr = f'{pokemonCall} used **{moveUsed}**! It missed!'
			case BattleAction.Failed:
				moveUsed = self.userattack if teamA else self.cpuattack
				turnStr = f'{pokemonCall} used **{moveUsed}**! But it failed!'
			case BattleAction.Defeated:
				turnStr = f'{pokemonCall} was knocked out!'
			case _:
				pass
		if pokemon.CurrentAilment == 1:
			turnStr = f'{pokemonCall} is paralyzed!\n{turnStr}'
		if pokemon.CurrentAilment == 4:
			turnStr = f'{turnStr}\n{pokemonCall} is hurt by the burn!'
		if pokemon.CurrentAilment == 5:
			turnStr = f'{turnStr}\n{pokemonCall} is hurt by the poison!'
		if pokemon.CurrentAilment == 6:
			turnStr = f'{pokemonCall} is confused!\n{turnStr}'
		if pokemon.CurrentAilment == 8:
			trapMove = self.battle.TeamATrapped if teamA else self.battle.TeamBTrapped
			turnStr = f'{turnStr}\n{pokemonCall} is hurt by **{trapMove.Name}**!'
		if opponent.CurrentAilment == 18:
			turnStr = f'{turnStr}\n{pokemonCall} is healed by **Leech Seed**!'
		if pokemon.CurrentAilment == 18:
			turnStr = f'{turnStr}\n{pokemonCall} is drained by **Leech Seed**!'

	async def Description(self):

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

		moveStr = f'{usrString if self.userfirst else cpuString}\n--------------------\n{cpuString if self.userfirst else usrString}'
		titleStr = f'__**A Wild {self.leader.Name} appeared!**__' if self.battle.IsWild else f'__**{self.leader.Name} wants to Battle!**__'
		return f'{titleStr}\n{moveStr}```{pkmnData}```'

	async def GetEmbeds(self):
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
