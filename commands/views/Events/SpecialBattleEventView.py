from datetime import UTC, datetime
import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from commands.views.Events.EventView import EventView

from globals import EventColor, FightReaction, ShortDateFormat
from middleware.decorators import trainer_check
from models.Gym import SpecialTrainer
from models.Pokemon import Pokemon, PokemonData
from models.Server import Server
from services import battleservice, itemservice, pokemonservice, serverservice, trainerservice
from services.utility import discordservice

class SpecialBattleEventView(EventView):

	def __init__(self, server: Server, channel: discord.TextChannel, sTrainer: SpecialTrainer):
		self.captureLog = logging.getLogger('capture')
		self.strainer = sTrainer
		self.sTeam = pokemonservice.GetPokemonByIdList(sTrainer.Team)
		self.userentries = []
		embed = discordservice.CreateEmbed(
				f'{sTrainer.Name} Wants To Battle!',
				self.TeamDesc(),
				EventColor)
		embed.set_image(url=sTrainer.Sprite)
		super().__init__(server, channel, embed)

	@discord.ui.button(label=FightReaction)
	@trainer_check
	async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id in self.userentries:
			return await interaction.followup.send(content=f"You already battled this trainer! Wait for more to show up in the future.", ephemeral=True)
		self.userentries.append(interaction.user.id)
		trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
		fight = battleservice.TeamFight(
			[{'Level': t.Level, 'Data': pokemonservice.GetPokemonById(t.Pokemon_Id)} for t in trainerservice.GetTeam(trainer)],
			[{'Level': 50 if p.Rarity <= 5 else 100, 'Data': p} for p in self.sTeam]
		)
		
		if not self.messagethread or not interaction.guild.get_channel_or_thread(self.messagethread.id):
			self.messagethread = await self.message.create_thread(
				name=f"{self.strainer.Name.replace(' ', '')}-{datetime.now(UTC).strftime(ShortDateFormat)}",
				auto_archive_duration=60)
			self.server.CurrentEvent.ThreadId = self.messagethread.id
			serverservice.UpsertServer(self.server)
			self.eventLog.info(f"{self.server.ServerName} - Created Thread")
		await self.messagethread.send(self.FightDesc(interaction.user.id, fight.count(2) < len(trainer.Team)))
		return await interaction.followup.send(content=self.ResultDesc(fight, trainerservice.GetTeam(trainer)), ephemeral=True)

	def FightDesc(self, userId: int, won: bool):
		if won:
			return f'<@{userId}> won and received an award!'
		return f'<@{userId}> was defeated. No reward given.'

	def TeamDesc(self):
		teamDesc: list[list] = []
		for i, t in enumerate(self.sTeam):
			teamDesc.append([f'{i+1}:', f'{t.Name}'])
		reward = f'{self.strainer.Amount}x {itemservice.GetPokeball(self.strainer.Reward).Name}(s)'
		pkmnData = t2a(
			body=teamDesc, 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f'Reward: **{reward}**```{pkmnData}```'

	def ResultDesc(self, fight: list[int], trainerTeam: list[Pokemon]):
		tTeamData = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainerTeam])
		first = second = 0
		battleArr = []
		for res in fight:
			#Team One Wins
			if res == 1:
				battleArr.append([f"\u001b[0;37m{tTeamData[first].Name}\u001b[0m",f"\u001b[0;31m{self.sTeam[second].Name}\u001b[0m"])
				second += 1
			#Team Two Wins
			else:
				battleArr.append([f"\u001b[0;31m{tTeamData[first].Name}\u001b[0m",f"\u001b[0;37m{self.sTeam[second].Name}\u001b[0m"])
				first += 1
		
		battle = t2a(
			body=battleArr, 
			first_col_heading=False,
			alignments=Alignment.CENTER,
			style=PresetStyle.markdown,
			cell_padding=2)
		
		return f"```ansi\n{battle}```\n{'You won!' if first < len(tTeamData) else 'You have been defeated.'}"