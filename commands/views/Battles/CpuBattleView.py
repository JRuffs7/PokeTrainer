import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from commands.views.Battles.BattleTools import ItemSelector, MoveSelector, PokemonSelector
from globals import Dexmark, Formmark, PokemonColor, WarningSign, to_dict
from middleware.decorators import defer
from models.Battle import BattleAction, CpuBattle
from models.Pokemon import Move, Pokemon
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import battleservice, itemservice, moveservice, pokemonservice, statservice, trainerservice
from services.utility import battleai, discordservice

class CpuBattleView(discord.ui.View):

	def __init__(self, trainer: Trainer, cpuName: str, cpuTeam: list[Pokemon], wildBattle: bool):
		self.battleLog = logging.getLogger('battle')
		self.trainer = trainer
		self.cpuname = cpuName
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.cputeam = cpuTeam
		self.wildbattle = wildBattle
		self.fleeattempts = 0
		self.currentturn = 0
		self.userfirst = False
		self.userpkmnchoice = None
		self.useritemchoice = None
		moveIds: list[int] = []
		pokeIds: list[int] = []
		for p in self.trainerteam + self.cputeam:
			moveIds.extend([m.MoveId for m in p.LearnedMoves if m.MoveId not in moveIds])
			if p.Pokemon_Id not in pokeIds:
				pokeIds.append(p.Pokemon_Id)
		self.battle = CpuBattle.from_dict({
			'IsWild': wildBattle,
			'TeamAPkmn': self.trainerteam[0],
			'TeamBPkmn': self.cputeam[0],
			'AllPkmnData': pokemonservice.GetPokemonByIdList(pokeIds),
			'AllMoveData': moveservice.GetMovesById(moveIds),
		})
		self.battle.reset_stats(True)
		self.battle.reset_stats(False)
		super().__init__(timeout=300)
		self.AddMainButtons()

	async def on_timeout(self):
		msg = f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))} (Lvl. {self.battle.TeamBPkmn.Level}) ran away!' if self.wildbattle else f'Battle with {self.cpuname} canceled. No exp given and all stats reset.'
		await self.message.edit(content=f'{msg}', embed=None, view=None)
		return await super().on_timeout()
	
	def AddMainButtons(self):
		for item in self.children:
			self.remove_item(item)

		attackbtn = discord.ui.Button(label="Attack", style=discord.ButtonStyle.primary, disabled=False)
		attackbtn.callback = self.attack_button
		pkmnbtn = discord.ui.Button(label="Pokemon", style=discord.ButtonStyle.secondary, disabled=((len([p for p in self.trainerteam if p.CurrentHP > 0 and p.Id != self.battle.TeamAPkmn.Id]) < 1) or (self.IsCharging(True))))
		pkmnbtn.callback = self.pokemon_button
		itembtn = discord.ui.Button(label="Items", style=discord.ButtonStyle.success, disabled=self.IsCharging(True))
		itembtn.callback = self.item_button
		runbtn = discord.ui.Button(label="Run", style=discord.ButtonStyle.danger, disabled=((not self.wildbattle) or (self.IsCharging(True))))
		runbtn.callback = self.run_button
		self.add_item(attackbtn)
		self.add_item(pkmnbtn)
		self.add_item(itembtn)
		self.add_item(runbtn)

	async def back_button(self, inter: discord.Interaction):
		self.AddMainButtons()
		await self.message.edit(view=self)

	#region Attack

	@defer
	async def attack_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
		self.useraction = BattleAction.Attack

		if self.IsCharging(True):
			lastUserMove = next(t for t in self.GetLastTurn() if t.TeamA).Move
			return await self.MoveSelection(None, str(lastUserMove.Id))
		
		if not battleservice.AbleToAttack(self.battle):
			return
		if [m for m in self.battle.TeamAPkmn.LearnedMoves if m.PP > 0]:
			self.add_item(MoveSelector(self.battle.TeamAPkmn.LearnedMoves))
			backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
			backBtn.callback = self.back_button
			self.add_item(backBtn)
			await self.message.edit(view=self)
		else:
			await self.MoveSelection(None, '165')

	async def MoveSelection(self, inter: discord.Interaction, choice: str): 
		self.userattack = moveservice.GetMoveById(int(choice))
		self.TakeTurn()

	#endregion

	#region Pokemon

	@defer
	async def pokemon_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
		if self.battle.TeamAPkmn and [p for p in self.trainerteam if p.CurrentHP > 0] > 1:
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
			self.TakeTurn(inter)


	#endregion

	#region Items

	@defer
	async def item_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
			
		ballBtn = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.primary, custom_id='pokeball', disabled=(not self.battle.IsWild or not itemservice.GetTrainerPokeballs(self.trainer)))
		ballBtn.callback = self.item_cat_button
		potionBtn = discord.ui.Button(label="Potions", style=discord.ButtonStyle.secondary, custom_id='potion', disabled=(not itemservice.GetTrainerPotions(self.trainer)))
		potionBtn.callback = self.item_cat_button
		backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
		backBtn.callback = self.back_button
		self.add_item(ballBtn)
		self.add_item(potionBtn)
		self.add_item(backBtn)
		await self.message.edit(view=self)
	
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
				await self.item_button(inter)
			else:
				self.add_item(PokemonSelector(available, self.battle.AllPkmnData))
				await self.message.edit(view=self)

	#endregion

	#region Run

	@defer
	async def run_button(self, inter: discord.Interaction):
		self.userAction = BattleAction.Flee
		self.userfirst = True
		self.fleeattempts += 1
		self.TakeTurn(inter)

	#endregion

	#region Move

	async def TakeTurn(self, inter: discord.Interaction):
		if self.useraction == BattleAction.Swap:
			self.userfirst = True
			self.battle.TeamAPkmn = self.userpkmnchoice
			self.battle.reset_stats(True)
			self.usermessage = f'You swapped in {pokemonservice.GetPokemonDisplayName(cpuObj, next(p for p in self.battle.AllPkmnData if p.Id == cpuObj.Pokemon_Id), False, False)}.'
		
		elif self.useraction == BattleAction.Pokeball:
			self.userfirst = True
			if trainerservice.TryCapture(self.useritemchoice, self.trainer, self.battle.TeamBPkmn):
				caughtMsg = f'<@{inter.user.id}> used a {self.useritemchoice.Name} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id))} (Lvl. {self.battle.TeamBPkmn.Level})**!'
				expMsg = f'\nYour entire team also gained some XP**' if trainerservice.HasRegionReward(self.trainer, 9) else ''
				trainerservice.UpsertTrainer(self.trainer)
				self.message.delete(0.1)
				self.stop()
				return await inter.followup.send(content=f'{caughtMsg}{expMsg}', embeds=[], view=None)
			self.usermessage = f'Used a {self.useritemchoice.Name}...it broke free!'
		
		elif self.useraction == BattleAction.Item:
			self.userfirst = True
			self.usermessage = f'You swapped in {pokemonservice.GetPokemonDisplayName(cpuObj, next(p for p in self.battle.AllPkmnData if p.Id == cpuObj.Pokemon_Id), False, False)}.'
		
		elif self.useraction == BattleAction.Flee:
			if self.fleeattempts == 3 or battleservice.FleeAttempt(self.battle, self.fleeattempts):
				self.stop()
				return await inter.followup.send(content=f'<@{inter.user.id}> ran away from **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}.**', embeds=[], view=None)
			self.userfirst = True
			self.usermessage = f"Attempted to run away but couldn't!"

		cpuObj = battleai.CpuAction(self.battle)
		if type(cpuObj) is Pokemon:
			self.battle.TeamBPkmn = cpuObj
			self.battle.reset_stats(False)
			self.cpumessage = f'The opponent swapped in {pokemonservice.GetPokemonDisplayName(cpuObj, next(p for p in self.battle.AllPkmnData if p.Id == cpuObj.Pokemon_Id), False, False)}.'
		
		if self.useraction == BattleAction.Attack:
			if type(cpuObj) is Move:
				self.userfirst = battleservice.TeamAAttackFirst(self.userattack, next(m for m in self.battle.AllMoveData if m.Id == cpuObj.MoveId), self.battle)
			
			


		self.AddMainButtons()
		await self.message.edit(embeds=self.GetEmbeds(), view=self)

	#endregion

	#region Other

	def GetLastTurn(self):
		return [tu for tu in self.battle.Turns if tu.TurnNum == self.currentturn-1]

	def IsCharging(self, teamA: bool):
		charging = next((t for t in self.GetLastTurn() if t.TeamA == teamA and t.Action == BattleAction.Charge),None)
		return charging is not None

	def Description(self):
		trainerPkData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamAPkmn.Pokemon_Id)
		cpuPkData = next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id)
		pkmnData = t2a(
			body=[
				[f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, trainerPkData, False, False)}', '|', f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, cpuPkData, False, False)}'],
				[f'Lvl. {self.battle.TeamAPkmn.Level}', '|', f'Lvl. {self.battle.TeamBPkmn.Level}'],
				[f'HP: {self.battle.TeamAPkmn.CurrentHP}/{statservice.GenerateStat(self.battle.TeamAPkmn, trainerPkData, StatEnum.HP)}', '|', f'HP: {self.battle.TeamBPkmn.CurrentHP}/{statservice.GenerateStat(self.battle.TeamBPkmn, cpuPkData, StatEnum.HP)}'], 
			], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.CENTER,Alignment.RIGHT],
			style=PresetStyle.plain,
			cell_padding=0)
		if self.battle.LastTeamAMove:
			tMove = f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamAPkmn, trainerPkData, False, False)} used {moveservice.GetMoveById(self.battle.LastTeamAMove).Name}.'
		else:
			tMove = ''
		if self.battle.LastTeamBMove:
			cMove = f'{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, cpuPkData, False, False)} used {moveservice.GetMoveById(self.battle.LastTeamBMove).Name}.'
		else:
			cMove = ''
		moveStr = f"\n{tMove if self.userfirst else cMove}\n{cMove if self.userfirst else tMove}" if tMove or cMove else ''
		titleStr = f'__**A Wild {self.cpuname} appeared!**__' if self.wildbattle else f'__**{self.cpuname} wants to Battle!**__'
		return f'{titleStr}{moveStr}```{pkmnData}```'

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
		self.message = await self.interaction.original_response()
