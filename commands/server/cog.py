import discord
from discord import app_commands
from discord.ext import commands

from globals import ServerDetailColor
from middleware.permissionchecks import is_admin
from models.CustomException import ServerInvalidException
from services import pokemonservice, serverservice
from services.utility import discordservice


class ServerCommands(commands.Cog, name="ServerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="start",
                        description="Start PokeTrainer in your server")
  @is_admin()
  async def start(self, inter: discord.Interaction, percent: int, delete: bool | None):

    print("START called")
    if inter.guild and 0 < percent < 101:
      serv = serverservice.StartServer(inter.guild_id, inter.channel_id,
                                       inter.guild.name, percent, delete or True)
      if serv:
        return await discordservice.SendMessage(inter, 'Server Details', serv,
                                                ServerDetailColor, True)
    return await discordservice.SendErrorMessage(inter, "Start")

  @app_commands.command(name="getserver",
                        description="(Admin only) Display server details")
  @is_admin()
  async def getserver(self, inter: discord.Interaction):
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
    print("TC called")
    try:
      serv = serverservice.ToggleChannel(inter.guild_id, inter.channel_id)
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
    except ServerInvalidException:
      return await discordservice.SendServerError(inter)

  @app_commands.command(
      name="editspawnchance",
      description=
      "(Admin only) Edit the spawn percentage for the server")
  @is_admin()
  async def editspawnchance(self, inter: discord.Interaction, percent: int):
    print("CHANGE PERCENT called")
    try:
      if 0 < percent < 101:
        serverservice.ChangePercent(inter.guild_id, percent)
        return await discordservice.SendMessage(inter, 'Spawn Chance Changed', 
                                         f'Spawn chance for the server changed to {percent}%', 
                                         ServerDetailColor, True)
      return await discordservice.SendErrorMessage(inter, 'editspawnchance')
    except ServerInvalidException:
      return await discordservice.SendServerError(inter)
    
  @app_commands.command(
      name="toggledeletespawn",
      description=
      "(Admin only) Toggles the deletion of previously spawned Pokemon messages")
  @is_admin()
  async def toggledeletespawn(self, inter: discord.Interaction):
    print("TOGGLE DELETE called")
    try:
      deleteSpawn = serverservice.ToggleDeleteSpawn(inter.guild_id)
      return await discordservice.SendMessage(inter, 'Delete Spawn Toggled', 
                                        'Previously spawned Pokemon will now be deleted' if deleteSpawn else 'Previously spawned Pokemon will remain in the chat channels', 
                                        ServerDetailColor, True)
    except ServerInvalidException:
      return await discordservice.SendServerError(inter)
    except Exception as e:
      print(f"{e}")


  @app_commands.command(
      name="stop",
      description="(Admin only) Stop PokeTrainer from operating in your server"
  )
  @is_admin()
  async def stop(self, inter: discord.Interaction):
    print("STOP called")
    try:
      stopped = serverservice.DeleteServer(inter.guild_id)
      if stopped:
        return await discordservice.SendMessage(
            inter, 'Server Stopped',
            "Thank you for using PokeTrainer. To begin again, use the **/start *percent*** command.",
            ServerDetailColor)
      return await discordservice.SendErrorMessage(inter, "Stop")
    except ServerInvalidException:
      return await discordservice.SendServerError(inter)

  @app_commands.command(
      name="testspawn",
      description="Spawns a test Pokemon in this channel. Cannot be caught")
  @is_admin()
  async def testspawn(self, inter: discord.Interaction):
    print("TEST SPAWN called")
    pkmn = pokemonservice.GetRandomSpawnPokemon()
    if pkmn:
      return await discordservice.SendPokemon(inter.guild_id, inter.channel_id,
                                              pkmn, True)
    return await discordservice.SendErrorMessage(inter, "TestSpawn")


async def setup(bot: commands.Bot):
  await bot.add_cog(ServerCommands(bot))
