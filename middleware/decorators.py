import functools
import logging
import functools

from globals import AdminList, EphemeralCommands
from services import serverservice, trainerservice
from services.utility import discordservice_permission


cmdLog = logging.getLogger('discord')
errLog = logging.getLogger('error')

def method_logger(function):
  @functools.wraps(function)
  async def wrapper(self, *args, **kwargs):
    try:
      cmdLog.info(f"{args[0].guild.name} - {function.__name__.upper()} command called")
      await args[0].response.defer(ephemeral=(function.__name__.lower() in EphemeralCommands))
      return await function(self, *args, **kwargs)
    except:
      # log the exception
      err = f"There was an exception in command '{function.__name__.upper()}'"
      errLog.exception(f"\nERROR - {function.__name__.upper()}\n{err}\n\n")
      
      # re-raise the exception
      raise
  return wrapper


def is_admin(function):
  @functools.wraps(function)
  async def wrapper(self, *args, **kwargs):
    if not args[0].permissions.administrator:
      await discordservice_permission.SendError(args[0], 'admin')
      return 
    return await function(self, *args, **kwargs)
  return wrapper


def is_bot_admin(function):
  @functools.wraps(function)
  async def wrapper(self, *args, **kwargs):
    if args[0].author.id not in AdminList:
      cmdLog.info(f'Sync Command attempted by {args[0].author.display_name} in server {args[0].guild.name}')
      return
    return await function(self, *args, **kwargs)
  return wrapper


def server_check(function):
  @functools.wraps(function)
  async def wrapper(self, *args, **kwargs):
    serv = serverservice.GetServer(args[0].guild_id)
    if not serv:
      await discordservice_permission.SendError(args[0], 'server')
      return
    return await function(self, *args, **kwargs)
  return wrapper

def trainer_check(function):
  @functools.wraps(function)
  async def wrapper(self, *args, **kwargs):
    inter = args[0]
    if not inter.response.is_done():
       await inter.response.defer()
    userId = next((int(o["value"]) for o in inter.data["options"] if o["type"] == 6), inter.user.id) if "options" in inter.data.keys() else inter.user.id
    trainer = trainerservice.GetTrainer(inter.guild_id, userId if userId else inter.user.id)
    if not trainer:
      await discordservice_permission.SendError(inter, 'trainer')
      return
    return await function(self, *args, **kwargs)
  return wrapper


def button_check(f):
	async def wrapper(self,*args):
		if args[0].user.id == self.user.id:
			return await f(self, *args) 
		return await args[0].response.defer()
	return wrapper