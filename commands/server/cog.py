import discord
from discord import app_commands
from discord.ext import commands

from globals import ServerDetailColor
from middleware.permissionchecks import is_admin
from services import serverservice
from services.utility import discordservice


class ServerCommands(commands.Cog, name="ServerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="register",
                        description="Register your server with PokeTrainer. Choose spawn % and if previous spawns should be deleted.")
  @is_admin()
  async def register(self, inter: discord.Interaction, percent: int, delete: bool | None):

    print("REGISTER called")
    if inter.guild and 0 < percent < 101:
      serv = serverservice.StartServer(inter.guild_id, inter.channel_id,
                                       inter.guild.name, percent, delete or True)
      if serv:
        return await discordservice.SendMessage(inter, 'Server Details', serv,
                                                ServerDetailColor, True)
    return await discordservice.SendErrorMessage(inter, "register")

  @app_commands.command(name="serverinfo",
                        description="(Admin only) Display server details")
  @is_admin()
  async def serverinfo(self, inter: discord.Interaction):
    print("GS called")
    serv = serverservice.GetServer(inter.guild_id)
    return await discordservice.SendMessage(
        inter, 'Server Details', serv if serv else
        "Server is not registered. Use **/start *percent*** command. Use **~help start** for more information.",
        ServerDetailColor, True)

  @app_commands.command(
      name="togglechannel",
      description=
      "(Admin only) Toggles the current channel for PokeTrainer spawns")
  @is_admin()
  async def togglechannel(self, inter: discord.Interaction):
    print("TOGGLE CHANNEL called")
    serv = serverservice.GetServer(inter.guild_id)
    if not serv:
      return await discordservice.SendServerError(inter)
    
    serv = serverservice.ToggleChannel(serv, inter.channel_id)
    if serv is None:
      return await discordservice.SendErrorMessage(inter, "ToggleChannel")
    elif serv:
      return await discordservice.SendMessage(
          inter, 'Channel Added', 'Channel added to server spawn list.',
          ServerDetailColor, True)
    else:
      return await discordservice.SendMessage(
          inter, 'Channel Removed',
          'Channel removed from server spawn list.', ServerDetailColor, True)
      

  @app_commands.command(
      name="editspawnchance",
      description=
      "(Admin only) Edit the spawn percentage for the server")
  @is_admin()
  async def editspawnchance(self, inter: discord.Interaction, percent: int):
    print("CHANGE PERCENT called")
    server = serverservice.GetServer(inter.guild_id)
    if not server:
      return await discordservice.SendServerError(inter)
    
    if 0 < percent < 101:
      serverservice.ChangePercent(server, percent)
      return await discordservice.SendMessage(inter, 'Spawn Chance Changed', 
                                        f'Spawn chance for the server changed to {percent}%', 
                                        ServerDetailColor, True)
    return await discordservice.SendErrorMessage(inter, 'editspawnchance')
    
  @app_commands.command(
      name="toggledeletespawn",
      description=
      "(Admin only) Toggles the deletion of previously spawned Pokemon messages")
  @is_admin()
  async def toggledeletespawn(self, inter: discord.Interaction):
    print("TOGGLE DELETE called")
    server = serverservice.GetServer(inter.guild_id)
    if not server:
      return await discordservice.SendServerError(inter)
    
    deleteSpawn = serverservice.ToggleDeleteSpawn(server)
    return await discordservice.SendMessage(inter, 'Delete Spawn Toggled', 
                                      'Previously spawned Pokemon will now be deleted' if deleteSpawn else 'Previously spawned Pokemon will remain in the chat channels', 
                                      ServerDetailColor, True)


  @app_commands.command(
      name="stop",
      description="(Admin only) Stop PokeTrainer from operating in your server"
  )
  @is_admin()
  async def stop(self, inter: discord.Interaction):
    print("STOP called")
    server = serverservice.GetServer(inter.guild_id)
    if not server:
      return await discordservice.SendServerError(inter)
    
    stopped = serverservice.DeleteServer(server)
    if stopped:
      return await discordservice.SendMessage(
          inter, 'Server Stopped',
          "Thank you for using PokeTrainer. To begin again, use the **/register *percent*** command.",
          ServerDetailColor)
    return await discordservice.SendErrorMessage(inter, "Stop")


async def setup(bot: commands.Bot):
  await bot.add_cog(ServerCommands(bot))
