import discord

from globals import TrainerColor
from middleware.decorators import defer
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from services.utility import discordservice


class WishlistView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = pokemonservice.GetPokemonByIdList(trainer.Wishlist)
		self.currentPage = 0
		super().__init__(timeout=300)
		if len(trainer.Wishlist) > 1:
			self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
			self.prevBtn.callback = self.page_button
			self.add_item(self.prevBtn)
		remBtn = discord.ui.Button(label="Remove", style=discord.ButtonStyle.green)
		remBtn.callback = self.remove_button
		self.add_item(remBtn)
		if len(trainer.Wishlist) > 1:
			self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
			self.nextBtn.callback = self.page_button
			self.add_item(self.nextBtn)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		pkmn = self.pokemon[self.currentPage]
		embed = discordservice.CreateEmbed(
				f'{self.interaction.user.display_name}s Wishlist',
				f'**__{pkmn.Name}__**',
				TrainerColor)
		embed.set_image(url=pkmn.Sprite)
		embed.set_footer(text=f'{self.currentPage+1}/{len(self.trainer.Wishlist)}')
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, interaction: discord.Interaction):
		if interaction.data['custom_id'] == 'prev':
			self.currentPage -= 1
		else:
			self.currentPage += 1
		self.prevBtn.disabled = self.currentPage == 0
		self.nextBtn.disabled = self.currentPage == len(self.pokemon)-1
		await self.update_message()

	@defer
	async def remove_button(self, interaction: discord.Interaction):
		await self.message.delete(delay=0.01)
		pkmn = self.pokemon[self.currentPage]
		self.trainer.Wishlist.remove(pkmn.Id)
		trainerservice.UpsertTrainer(self.trainer)
		await interaction.followup.send(content=f'{pkmn.Name} has been removed from your wishlist.', ephemeral=True)
