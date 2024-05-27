import functools
import logging
import functools

from globals import AdminList
from services import serverservice, trainerservice
from services.utility import discordservice_permission


cmdLog = logging.getLogger('command')
errLog = logging.getLogger('error')

def method_logger(eph: bool = False):
  def inner_decor(function):
    @functools.wraps(function)
    async def wrapper(self, *args, **kwargs):
      try:
        if not args[0].guild:
          return
        await args[0].response.defer(ephemeral=eph)
        cmdLog.info(f"{args[0].guild.name} - {function.__name__.upper()} command called")
        return await function(self, *args, **kwargs)
      except Exception as e:
        errorStr = str(e)
        if '404' in errorStr:
          # log the exception
          errLog.exception(f"\nERROR - 404 exception in command '{function.__name__.upper()}'\n")
          return
        else:
          # log the exception
          errLog.exception(f"\nERROR - {function.__name__.upper()}\n{errorStr}\n")
    return wrapper
  return inner_decor


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
    inter = args[0]
    if not inter.response.is_done():
       await inter.response.defer()
    serv = serverservice.GetServer(inter.guild_id)
    if not serv:
      await discordservice_permission.SendError(inter, 'server')
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
    if not trainerservice.CheckTrainer(inter.guild_id, userId if userId else inter.user.id):
      await discordservice_permission.SendError(inter, 'trainer')
      return
    return await function(self, *args, **kwargs)
  return wrapper


def defer(f):
  async def wrapper(self,*args):
    await args[0].response.defer()
    return await f(self, *args) 
  return wrapper