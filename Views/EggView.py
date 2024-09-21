from math import ceil
import discord

from globals import Dexmark, TrainerColor
from middleware.decorators import defer
from models.Egg import TrainerEgg
from models.Trainer import Trainer
from services import commandlockservice, itemservice, pokemonservice, trainerservice
from services.utility import discordservice


class EggView(discord.ui.View):

	def __init__(self, user: discord.User|discord.Member, trainer: Trainer, images: bool, ownEggs: bool):
		self.user = user
		self.trainer = trainer
		self.owneggs = ownEggs
		self.currentpage = 1
		self.images = images
		super().__init__(timeout=300)
		if self.images:
			if len(trainer.Eggs) > 1:
				self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
				self.prevBtn.callback = self.page_button
				self.add_item(self.prevBtn)
			if self.owneggs:
				htchbtn = discord.ui.Button(label="Hatch", style=discord.ButtonStyle.green)
				htchbtn.callback = self.hatch_button
				self.add_item(htchbtn)
			if len(trainer.Eggs) > 1:
				self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
				self.nextBtn.callback = self.page_button
				self.add_item(self.nextBtn)
		elif self.owneggs:
			htchbtn = discord.ui.Button(label="Hatch All", style=discord.ButtonStyle.green)
			htchbtn.callback = self.hatch_button
			self.add_item(htchbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.user.display_name}'s Egg List",
				self.SingleEmbedDesc() if self.images else self.ListEmbedDesc(),
				TrainerColor)
		if self.images == 1:
			embed.set_image(url=itemservice.GetEgg(self.trainer.Eggs[self.currentpage-1].EggId).Sprite)
			embed.set_footer(text=f"{self.currentpage}/{len(self.trainer.Eggs)}")
		else:
			embed.set_thumbnail(url=self.user.display_avatar.url)
		await self.message.edit(embed=embed, view=self)
	
	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'prev':
			self.currentpage -= 1
		else:
			self.currentpage += 1
		self.prevBtn.disabled = self.currentpage == 1
		self.nextBtn.disabled = self.currentpage == len(self.trainer.Eggs)
		await self.update_message()

	@defer
	async def hatch_button(self, inter: discord.Interaction):
		if not self.owneggs:
			return
		if commandlockservice.IsLocked(self.trainer.ServerId, self.trainer.UserId):
			return await self.message.edit(content=f'You are in the middle of another interaction. Complete that operation, then try again.')
		
		hatchMessage = None
		if self.images:
			egg = self.trainer.Eggs[self.currentpage-1]
			hatch = trainerservice.TryHatchEgg(self.trainer, egg.Id)
			if hatch:
				hatchMessage = f'{itemservice.GetEgg(egg.EggId).Name} hatched into a **{pokemonservice.GetPokemonDisplayName(hatch)}**'
		else:
			hatchArr: list[str] = []
			for i in self.trainer.Eggs:
				hatch = trainerservice.TryHatchEgg(self.trainer, i.Id)
				if hatch:
					hatchArr.append(f'{itemservice.GetEgg(i.EggId).Name} hatched into a **{pokemonservice.GetPokemonDisplayName(hatch)}**')
			if hatchArr:
				hatchMessage = '\n'.join(hatchArr)
		
		if hatchMessage:
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
			trainerservice.UpsertTrainer(self.trainer)
			self.clear_items()
			await self.message.edit(content=hatchMessage, embeds=[], view=None)
			self.stop()
		else:
			await self.message.edit(content=f'Nothing to hatch! Progress your eggs by using the **/spawn** command!')

	def SingleEmbedDesc(self):
		egg = self.trainer.Eggs[self.currentpage-1]
		eggData = itemservice.GetEgg(egg.EggId)
		return f'**__{eggData.Name}{f" {Dexmark}" if egg.SpawnCount == eggData.SpawnsNeeded else ""}__**\nGeneration: {egg.Generation}\nProgress (/spawn): {egg.SpawnCount}/{eggData.SpawnsNeeded}'

	def ListEmbedDesc(self):
		return '\n'.join([f'{itemservice.GetEgg(egg.EggId).Name} ({egg.SpawnCount}/{itemservice.GetEgg(egg.EggId).SpawnsNeeded}){f" {Dexmark}" if egg.SpawnCount == itemservice.GetEgg(egg.EggId).SpawnsNeeded else ""}' for egg in self.trainer.Eggs])

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()