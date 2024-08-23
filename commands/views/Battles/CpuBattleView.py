import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment

from commands.views.Battles.BattleTools import MoveSelector, PokemonSelector
from globals import Dexmark, Formmark, PokemonColor, WarningSign
from middleware.decorators import defer
from models.Battle import BattleAction, CpuBattle
from models.Pokemon import Pokemon
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import battleservice, moveservice, pokemonservice, statservice, trainerservice
from services.utility import discordservice

class CpuBattleView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer, cpuName: str, cpuTeam: list[Pokemon], wildBattle: bool):
		self.battleLog = logging.getLogger('battle')
		self.interaction = interaction
		self.trainer = trainer
		self.cpuname = cpuName
		self.trainerteam = trainerservice.GetTeam(trainer).copy()
		self.cputeam = cpuTeam
		self.wildbattle = wildBattle
		self.fleeattempts = 0
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
			'AllMoveData': moveservice.GetMovesById(moveIds)
		})
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
		pkmnbtn = discord.ui.Button(label="Pokemon", style=discord.ButtonStyle.secondary, disabled=(len(self.trainerteam) <= 1))
		pkmnbtn.callback = self.pokemon_button
		itembtn = discord.ui.Button(label="Items", style=discord.ButtonStyle.success, disabled=False)
		itembtn.callback = self.item_button
		runbtn = discord.ui.Button(label="Run", style=discord.ButtonStyle.danger, disabled=(not self.wildbattle))
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
		self.userAction = BattleAction.Attack
		if [m for m in self.battle.TeamAPkmn.LearnedMoves if m.PP > 0]:
			self.add_item(MoveSelector(self.battle.TeamAPkmn.LearnedMoves))
			backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
			backBtn.callback = self.back_button
			self.add_item(backBtn)
			await self.message.edit(view=self)
		else:
			return await MoveSelector(None, '165')

	async def MoveSelection(self, inter: discord.Interaction, choice: str):
		self.cpuaction = battleservice.CpuAction(self.battle)
		self.useraction = next(m for m in self.battle.TeamAPkmn.LearnedMoves if m.MoveId == int(choice))
		self.AddMainButtons()
		await self.message.edit(embeds=self.GetEmbeds(), view=self)

	#endregion

	#region Pokemon

	@defer
	async def pokemon_button(self, inter: discord.Interaction):
		for item in self.children:
			self.remove_item(item)
		self.userAction = BattleAction.Swap
		if self.battle.TeamAPkmn and len(self.trainerteam) > 1:
			self.add_item(PokemonSelector(self.trainerteam, self.battle.AllPkmnData, self.battle.TeamAPkmn))
			backBtn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, disabled=False)
			backBtn.callback = self.back_button
			self.add_item(backBtn)
			await self.message.edit(view=self)
	
	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		self.battle.TeamAPkmn = next(p for p in self.trainerteam if p.Id == choice)
		self.AddMainButtons()
		await self.message.edit(embeds=self.GetEmbeds(), view=self)

	#endregion

	#region Items

	@defer
	async def item_button(self, inter: discord.Interaction):
		self.userAction = BattleAction.Item
		self.battle.TeamAFirst = True
		await self.message.edit(view=self)

	#endregion

	#region Run

	@defer
	async def run_button(self, inter: discord.Interaction):
		self.userAction = BattleAction.Flee
		self.fleeattempts += 1
		if self.fleeattempts == 3 or battleservice.FleeAttempt(self.battle, self.fleeattempts):
			await self.message.edit(content=f'You ran away from **{pokemonservice.GetPokemonDisplayName(self.battle.TeamBPkmn, next(p for p in self.battle.AllPkmnData if p.Id == self.battle.TeamBPkmn.Pokemon_Id), False, False)}.**', embeds=[], view=None)
			self.stop()
		else:
			self.battle.TeamAFirst = True
			return

	#endregion

	#region Other

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
		moveStr = f"\n{tMove if self.battle.TeamAFirst else cMove}\n{cMove if self.battle.TeamAFirst else tMove}" if tMove or cMove else ''
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

	async def send(self):
		await self.interaction.followup.send(embeds=self.GetEmbeds(), view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
