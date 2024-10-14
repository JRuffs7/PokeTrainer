from discord import Interaction, Member, app_commands
from discord.ext import commands

from commands.autofills.autofills import autofill_tradable
from Views.TradeView import TradeView
from middleware.decorators import command_lock, elitefour_check, method_logger, trainer_check
from services import commandlockservice, pokemonservice, trainerservice
from services.utility import discordservice_trade

class TradeCommands(commands.Cog, name="TradeCommands"):

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	async def autofill_trade(self, inter: Interaction, current: str):
		data = []
		if 'user' not in inter.namespace:
			data.append(app_commands.Choice(name='Select User to trade with.',value=-1))
			return data
		user = inter.namespace['user']
		if user.id == inter.user.id:
			data.append(app_commands.Choice(name='Select User to trade with.',value=-1))
			return data

		trainer = trainerservice.GetTrainer(inter.guild_id, user.id)
		if not trainer:
			data.append(app_commands.Choice(name='Trainer does not exist.',value=-1))
			return data
		
		pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Id not in trainer.Team and p.Id not in trainer.Daycare])
		if not trainer:
			data.append(app_commands.Choice(name='No Pokemon available for trade.',value=-1))
			return data
		pkmnList.sort(key=lambda x: x.Name)
		for pkmn in pkmnList:
			if current.lower() in pkmn.Name.lower():
				data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
			if len(data) == 25:
				break
		return data


	@app_commands.command(name="trade",
												description="Trade with another user in the server.")
	@app_commands.autocomplete(give=autofill_tradable,receive=autofill_trade)
	@method_logger(True)
	@trainer_check
	@elitefour_check
	@command_lock
	async def trade(self, inter: Interaction, user: Member, give: int, receive: int):
		userTrainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
		userTradeList = [x for x in userTrainer.OwnedPokemon if x.Pokemon_Id == give and x.Id not in userTrainer.Team and x.Id not in userTrainer.Daycare]
		userTradeData = pokemonservice.GetPokemonById(give)
		if not userTradeList or not userTradeData:
			commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
			return await discordservice_trade.PrintTradeResponse(inter, 0, [userTradeData.Name if userTradeData else 'N/A'])
		targetTrainer = trainerservice.GetTrainer(inter.guild_id, user.id)
		targetTradeList = [x for x in targetTrainer.OwnedPokemon if x.Pokemon_Id == receive and x.Id not in targetTrainer.Team and x.Id not in targetTrainer.Daycare]
		targetTradeData = pokemonservice.GetPokemonById(receive)
		if not targetTradeList or not targetTradeData:
			commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
			return await discordservice_trade.PrintTradeResponse(inter, 1, [user.display_name, targetTradeData.Name if targetTradeData else 'N/A'])
		await TradeView(userTrainer, targetTrainer, userTradeList, targetTradeList, userTradeData, targetTradeData).send(inter)

async def setup(bot: commands.Bot):
	await bot.add_cog(TradeCommands(bot))
