from discord import app_commands, Interaction
from discord.ext import commands

from globals import discordLink
from middleware.decorators import method_logger, is_admin, server_check
from services import serverservice
from services.utility import discordservice_server

class ServerCommands(commands.Cog, name="ServerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="register",
                        description="Register the current channel with PokeTrainer.")
  @method_logger(True)
  @is_admin
  async def register(self, inter: Interaction):
    if not inter.guild_id or not inter.channel_id:
      return await discordservice_server.PrintRegisterResponse(inter, 0, [])
    serv = serverservice.RegisterServer(inter.guild_id, inter.channel_id, inter.guild.name)
    return await discordservice_server.PrintRegisterResponse(inter, 1, [serv.ServerName, serv.ChannelId, serv.CurrentEvent.EventName if serv.CurrentEvent else '', discordLink])

  @app_commands.command(name="server",
                        description="Display server details.")
  @method_logger(True)
  @server_check
  async def server(self, inter: Interaction):
    serv = serverservice.GetServer(inter.guild_id)
    return await discordservice_server.PrintServerResponse(inter, 0, [serv.ServerName, serv.ChannelId, serv.CurrentEvent.EventName if serv.CurrentEvent else ''])

  @app_commands.command(name="unregister",
      description="(Admin only) Remove your server from PokeTrainer."
  )
  @method_logger(True)
  @is_admin
  @server_check
  async def unregister(self, inter: Interaction):
    server = serverservice.GetServer(inter.guild_id)
    serverservice.DeleteServer(server)
    return await discordservice_server.PrintUnregisterResponse(inter, 0, [])


  @app_commands.command(name="invite",
      description="Invite this bot to another server!"
  )
  @method_logger(False)
  async def invite(self, inter: Interaction):
    return await discordservice_server.PrintInviteResponse(inter, 0, [])

async def setup(bot: commands.Bot):
  await bot.add_cog(ServerCommands(bot))
