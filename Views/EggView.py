import discord

from globals import Dexmark, TrainerColor, region_name
from middleware.decorators import defer
from models.Trainer import Trainer
from services import commandlockservice, pokemonservice, trainerservice
from services.utility import discordservice


class EggView(discord.ui.View):

	def __init__(self, user: discord.User|discord.Member, trainer: Trainer, images: bool, ownEggs: bool):
		self.user = user
		self.trainer = trainer
		self.owneggs = ownEggs
		self.currentpage = 1
		self.totalpages = len(trainer.Eggs) if images else 1
		self.images = images
		super().__init__(timeout=300)
		if self.images:
			if len(trainer.Eggs) > 1:
				self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, custom_id='prev')
				self.prevBtn.callback = self.page_button
				self.add_item(self.prevBtn)
			if self.owneggs:
				htchbtn = discord.ui.Button(label="Hatch", style=discord.ButtonStyle.green)
				htchbtn.callback = self.hatch_button
				self.add_item(htchbtn)
			if len(trainer.Eggs) > 1:
				self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, custom_id='next')
				self.nextBtn.callback = self.page_button
				self.add_item(self.nextBtn)
		elif self.owneggs:
			htchbtn = discord.ui.Button(label="Hatch All", style=discord.ButtonStyle.green)
			htchbtn.callback = self.hatch_button
			self.add_item(htchbtn)
		clsbtn = discord.ui.Button(label="Close", style=discord.ButtonStyle.gray)
		clsbtn.callback = self.close_button
		self.add_item(clsbtn)

	async def on_timeout(self):
		if self.owneggs:
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.user.display_name}'s Egg List",
				self.SingleEmbedDesc() if self.images else self.ListEmbedDesc(),
				TrainerColor,
				image=(self.trainer.Eggs[self.currentpage-1].Sprite if self.images else None),
				thumbnail=(self.user.display_avatar.url if not self.images else None),
				footer=(f"{self.currentpage}/{self.totalpages}" if self.images else None))
		await self.message.edit(embed=embed, view=self)
	
	@defer
	async def close_button(self, inter: discord.Interaction):
		await self.on_timeout()

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'prev':
			self.currentpage = (self.currentpage - 1) if self.currentpage > 1 else self.totalpages
		else:
			self.currentpage = (self.currentpage + 1) if self.currentpage < self.totalpages else 1
		await self.update_message()

	@defer
	async def hatch_button(self, inter: discord.Interaction):
		if not self.owneggs or inter.user.id != self.user.id:
			return
	
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		hatchMessage = None
		if self.images:
			egg = self.trainer.Eggs[self.currentpage-1]
			hatch = trainerservice.TryHatchEgg(self.trainer, egg)
			if hatch:
				hatchMessage = f'Egg ({region_name(egg.Generation)}) hatched into a **{pokemonservice.GetPokemonDisplayName(hatch)}**!\nGained **$100**'
		else:
			hatchArr: list[str] = []
			for i in self.trainer.Eggs:
				hatch = trainerservice.TryHatchEgg(self.trainer, i)
				if hatch:
					hatchArr.append(f'Egg ({region_name(i.Generation)}) hatched into a **{pokemonservice.GetPokemonDisplayName(hatch)}**')
			if hatchArr:
				hatchMessage = '\n'.join(hatchArr) + f'\nGained **${100*len(hatchArr)}**'
		
		if hatchMessage:
			self.clear_items()
			trainerservice.UpsertTrainer(self.trainer)
			await self.message.edit(content=hatchMessage, embeds=[], view=None)
			self.stop()
		else:
			await self.message.edit(content=f'Nothing to hatch! Progress your eggs by using the **/spawn** command!')

	def SingleEmbedDesc(self):
		egg = self.trainer.Eggs[self.currentpage-1]
		return f'**__Egg ({region_name(egg.Generation)})__**{f" {Dexmark}" if egg.SpawnCount == egg.SpawnsNeeded else ""}\nProgress (/spawn): {egg.SpawnCount}/{egg.SpawnsNeeded}'

	def ListEmbedDesc(self):
		return '\n'.join([f'Egg ({region_name(egg.Generation)}) - {egg.SpawnCount}/{egg.SpawnsNeeded}{f" {Dexmark}" if egg.SpawnCount == egg.SpawnsNeeded else ""}' for egg in self.trainer.Eggs])

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()