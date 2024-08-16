import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import Dexmark, FightReaction, Formmark, GreatBallReaction, PokeballReaction, PokemonColor, UltraBallReaction, WarningSign
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import battleservice, pokemonservice, statservice, trainerservice
from services.utility import discordservice

class CpuBattleView(discord.ui.View):
	mainButtons = []
	itemButtons = []

	def __init__(self, interaction: discord.Interaction, trainer: Trainer, cpuName: str, cpuTeam: list[Pokemon], wildBattle: bool):
		self.battleLog = logging.getLogger('battle')
		self.interaction = interaction
		self.trainer = trainer
		self.trainerteam = trainerservice.GetTeam(trainer)
		self.currentpkmn = self.trainerteam[0]
		self.cpuname = cpuName
		self.cputeam = cpuTeam
		self.allpkmndata = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in self.trainerteam]+[p.Pokemon_Id for p in cpuTeam])
		moves = []
		for p in self.trainerteam+cpuTeam:
			for m in p.LearnedMoves:
				if m not in moves:
					moves.append(m)
		self.allmovedata = battleservice.GetMovesById(moves)
		self.wildbattle = wildBattle
		self.traineraccuracy = 100
		self.cpuaccuracy = 100
		self.trainerevasion = 100
		self.cpuevasion = 100
		super().__init__(timeout=600)
		attackbtn = discord.ui.Button(label="Fight", style=discord.ButtonStyle.primary, disabled=False)
		attackbtn.callback = self.attack_button
		ballbtn = discord.ui.Button(label="Swap", style=discord.ButtonStyle.secondary, disabled=False)
		ballbtn.callback = self.ball_button
		itembtn = discord.ui.Button(label="Items", style=discord.ButtonStyle.success, disabled=False)
		itembtn.callback = self.item_button
		runbtn = discord.ui.Button(label="Run", style=discord.ButtonStyle.danger, disabled=(not wildBattle))
		runbtn.callback = self.run_button
		self.mainButtons.append(attackbtn)
		self.mainButtons.append(ballbtn)
		self.mainButtons.append(itembtn)
		self.mainButtons.append(runbtn)

		catchbtn = discord.ui.Button(label="Catch", style=discord.ButtonStyle.primary, disabled=False)
		catchbtn.callback = self.catch_button
		healbtn = discord.ui.Button(label="Heal", style=discord.ButtonStyle.success, disabled=False)
		healbtn.callback = self.heal_button
		curebtn = discord.ui.Button(label="Cure", style=discord.ButtonStyle.secondary, disabled=False)
		curebtn.callback = self.cure_button
		self.itemButtons.append(catchbtn)
		self.itemButtons.append(healbtn)
		self.itemButtons.append(curebtn)

		self.AddMainButtons(None)

	async def on_timeout(self):
		await self.message.edit(content=f'{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level}) ran away!', embed=None, view=None)
		return await super().on_timeout()
	
	async def AddMainButtons(self, interaction: discord.Interaction):
		for item in self.children:
			if type(item) is discord.ui.Button:
				self.remove_item(item)
		
		for i in self.mainButtons:
			self.add_item(i) 

	async def attack_button(self, interaction: discord.Interaction):
		for item in self.children:
			if type(item) is discord.ui.Button:
				self.remove_item(item)

		for m in self.currentpkmn.LearnedMoves:
			move = next(mo for mo in self.allmovedata if mo.Id == m)
			mvbtn = discord.ui.Button(label=move.Name, style=discord.ButtonStyle.secondary, disabled=False, custom_id=str(move.Id))
			mvbtn.callback = self.move_button
			self.add_item(mvbtn)

	async def move_button(self, interaction: discord.Interaction, button: discord.ui.Button):
			move = next(mo for mo in self.allmovedata if mo.Id == int(button.custom_id))
			battleservice.Attack(attack, attackdata, defend, defenddata, move)


	@discord.ui.button(label='Continue')
	@defer
	async def pokeball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not self.pressed:
			self.pressed = True
			await self.TryCapture(interaction, button.label, "Pokeball")

	def GetTitle(self):
		hasDexmark = Dexmark if ((self.pkmndata.PokedexId in self.trainer.Pokedex) if not self.pokemon.IsShiny else (self.pkmndata.Id in self.trainer.Shinydex)) else ''
		hasFormmark = Formmark if ((self.pkmndata.Id in self.trainer.Formdex) if not self.pokemon.IsShiny else False) else ''
		return f'{f"{hasDexmark}{hasFormmark} " if hasDexmark or hasFormmark else ""}{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})'

	def TrainerHealthString(self, trainer: Trainer):
		return f"{trainer.Health}{WarningSign}" if trainer.Health < 10 else f"{trainer.Health}"

	def PokemonDesc(self):
		pkmnData = t2a(
			body=[
				['Rarity:', f"{self.pkmndata.Rarity}", '|', 'Height:', self.pokemon.Height],
				['Color:',f"{self.pkmndata.Color}", '|','Weight:', self.pokemon.Weight], 
				['Types:', f"{'/'.join([statservice.GetType(t).Name for t in self.pkmndata.Types])}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"```{pkmnData}```"

	async def send(self):
		if not self.pokemon:
			return await self.interaction.followup.send("Failed to spawn a Pokemon. Please try again.", ephemeral=True)
		await self.interaction.followup.send(view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
		embed = discordservice.CreateEmbed(
				self.GetTitle(),
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(self.pokemon, self.pkmndata))
		embed.set_footer(text='Set Your Battle Pokemon Below')
		await self.message.edit(content=f'Current Trainer HP: {self.TrainerHealthString(self.trainer)}', embed=embed, view=self)
