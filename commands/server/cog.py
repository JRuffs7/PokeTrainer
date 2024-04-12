from discord import app_commands, Interaction
from discord.ext import commands

from middleware.decorators import method_logger, is_admin, server_check
from services import serverservice
from services.utility import discordservice_server

class ServerCommands(commands.Cog, name="ServerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="register",
                        description="Register your server for PokeTrainer events. Current channel will be used for any events.")
  @method_logger
  @is_admin
  async def register(self, inter: Interaction):
    if inter.guild:
      serv = serverservice.RegisterServer(inter.guild_id, inter.channel_id, inter.guild.name)
      return await discordservice_server.PrintRegisterResponse(inter, serv)

  @app_commands.command(name="server",
                        description="(Admin only) Display server details.")
  @method_logger
  @is_admin
  @server_check
  async def server(self, inter: Interaction):
    serv = serverservice.GetServer(inter.guild_id)
    return await discordservice_server.PrintServerResponse(inter, serv)

  @app_commands.command(
      name="swapchannel",
      description=
      "(Admin only) Toggles the current channel for PokeTrainer spawns")
  @method_logger
  @is_admin
  @server_check
  async def swapchannel(self, inter: Interaction):
    serv = serverservice.GetServer(inter.guild_id)
    serv = serverservice.SwapChannel(serv, inter.channel_id)
    return await discordservice_server.PrintSwapChannelResponse(inter, serv is not None)
      

  @app_commands.command(
      name="unregister",
      description="(Admin only) Stop PokeTrainer from operating in your server"
  )
  @method_logger
  @is_admin
  @server_check
  async def unregister(self, inter: Interaction):
    server = serverservice.GetServer(inter.guild_id)
    serverservice.DeleteServer(server)
    return await discordservice_server.PrintUnregisterResponse(inter)


  @app_commands.command(
      name="invite",
      description="Invite this bot to another server!"
  )
  @method_logger
  async def invite(self, inter: Interaction):
    return await discordservice_server.PrintInviteResponse(inter)

async def setup(bot: commands.Bot):
  await bot.add_cog(ServerCommands(bot))
