from discord import app_commands, Interaction
from discord.ext import commands
from Views.Shop.ShopView import ShopView
from middleware.decorators import command_lock, method_logger, trainer_check
from models.Move import MoveData
from services import commandlockservice, itemservice, moveservice, trainerservice
from services.utility import discordservice_shop


class ShopCommands(commands.Cog, name="ShopCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="viewshop",
                        description="View items available for sale.")
  @app_commands.choices(items=[
      app_commands.Choice(name="Pokeballs", value='pokeball'),
      app_commands.Choice(name="Potions", value='potion'),
      app_commands.Choice(name="Candy", value='candy'),
      app_commands.Choice(name="Evolution Items", value='evolution'),
      app_commands.Choice(name="TMs", value='tm')
  ])
  @method_logger(True)
  async def viewshop(self, inter: Interaction, items: str|None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    await ShopView(trainer, items).send(inter)

  async def buy_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[int]]:
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    choices = []
    if trainer:
      allItems = [i for i in itemservice.GetAllItems() if i.BuyAmount and i.BuyAmount <= trainer.Money]+[m for m in moveservice.GetTMMoves() if m.Cost and m.Cost <= trainer.Money]
      if not allItems:
        choices.append(app_commands.Choice(name=f'Not enough funds!',value='n/a'))
      else:
        allItems.sort(key=lambda x: x.Name)
        for i in allItems:
          if current.lower() in i.Name.lower():
            name = f'TM-{i.Name}' if type(i) is MoveData else i.Name
            choices.append(app_commands.Choice(name=f'{name} - ${i.Cost if type(i) is MoveData else i.BuyAmount}',value=f'm{i.Id}' if type(i) is MoveData else f'i{i.Id}'))
          if len(choices) == 25:
            break
    else:
      choices.append(app_commands.Choice(name=f'Create a Trainer first!',value='n/a'))
    return choices

  @app_commands.command(name="buy",
                        description="Buy items.")
  @app_commands.autocomplete(item=buy_autocomplete)
  @method_logger(False)
  @trainer_check
  @command_lock
  async def buy(self, inter: Interaction, item: str, amount: int):
    if item == 'n/a':
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_shop.PrintBuyResponse(inter, 0, [])
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if item.startswith('m'):
      it = moveservice.GetMoveById(int(item[1:]))
      if it.Cost > trainer.Money:
        commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
        return await discordservice_shop.PrintBuyResponse(inter, 0, [])
      amount = min(trainer.Money // it.Cost, amount)
      cost = (it.Cost*amount)
      trainerservice.ModifyItemList(trainer, it.MachineID, amount)
      trainer.Money -= cost
    else:
      it = itemservice.GetItem(int(item[1:]))
      if it.BuyAmount > trainer.Money:
        commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
        return await discordservice_shop.PrintBuyResponse(inter, 0, [])
      amount = min(trainer.Money // it.BuyAmount, amount)
      cost = (it.BuyAmount*amount)
      trainerservice.ModifyItemList(trainer, str(it.Id), amount)
      trainer.Money -= cost
    trainerservice.UpsertTrainer(trainer)
    commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
    return await discordservice_shop.PrintBuyResponse(inter, 1, [amount, it.Name, cost, trainer.Money])


  async def sell_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[int]]:
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    choices = []
    if trainer:
      if not [i for i in trainer.Items if trainer.Items[i] > 0]:
        choices.append(app_commands.Choice(name=f'No items to sell!',value='n/a'))
      else:
        allItems = [i for i in itemservice.GetAllItems() if str(i.Id) in trainer.Items and trainer.Items[str(i.Id)] > 0]+[m for m in moveservice.GetTMMoves() if m.MachineID in trainer.Items and trainer.Items[m.MachineID] > 0]
        allItems.sort(key=lambda x: x.Name)
        for i in allItems:
          if current.lower() in i.Name.lower():
            name = f'TM-{i.Name}' if type(i) is MoveData else i.Name
            choices.append(app_commands.Choice(name=f'{name} - ${int(i.Cost/2) if type(i) is MoveData else i.SellAmount}',value=f'm{i.Id}' if type(i) is MoveData else f'i{i.Id}'))
          if len(choices) == 25:
            break
    else:
      choices.append(app_commands.Choice(name=f'Create a Trainer first!',value='n/a'))
    return choices

  @app_commands.command(name="sell",
                        description="Sell items.")
  @app_commands.autocomplete(item=sell_autocomplete)
  @method_logger(False)
  @trainer_check
  @command_lock
  async def sell(self, inter: Interaction, item: str, amount: int):
    if item == 'n/a':
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_shop.PrintSellResponse(inter, 0, [])
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if item.startswith('m'):
      it = moveservice.GetMoveById(int(item[1:]))
      if it.MachineID not in trainer.Items or trainer.Items[it.MachineID] <= 0:
        commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
        return await discordservice_shop.PrintSellResponse(inter, 0, [])
      name = f'TM-{it.Name}'
      amount = min(trainer.Items[it.MachineID], amount)
      cost = int((it.Cost/2)*amount)
      trainerservice.ModifyItemList(trainer, it.MachineID, (0-amount))
      trainer.Money += cost
    else:
      it = itemservice.GetItem(int(item[1:]))
      if str(it.Id) not in trainer.Items or trainer.Items[str(it.Id)] <= 0:
        commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
        return await discordservice_shop.PrintSellResponse(inter, 0, [])
      name = it.Name
      amount = min(trainer.Items[str(it.Id)], amount)
      cost = int(it.SellAmount*amount)
      trainerservice.ModifyItemList(trainer, str(it.Id), (0-amount))
      trainer.Money += cost
    trainerservice.UpsertTrainer(trainer)
    commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
    return await discordservice_shop.PrintSellResponse(inter, 1, [amount, name, cost, trainer.Money])

async def setup(bot: commands.Bot):
  await bot.add_cog(ShopCommands(bot))
