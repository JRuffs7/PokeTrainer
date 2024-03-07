import discord
from discord import Embed, Interaction

import discordbot
from globals import ErrorColor
from dataaccess.utility.jsonreader import GetJson


async def SendErrorMessage(interaction, command):
  helpObj = helpservice.BuildCommandHelp(
      command, interaction.user.guild_permissions.administrator)
  if helpObj:
    return await interaction.response.send_message(embed=CreateEmbed(
        f'{helpObj.Name} Command Usage', helpObj.HelpString, ErrorColor),
                                            ephemeral=True)
  return await interaction.response.send_message(embed=CreateEmbed(
        f'{command} Command Usage', "You do not have permission to use this command. Inquire a server administrator for further details.", ErrorColor),
                                            ephemeral=True)


async def SendMessage(interaction, title, desc, color, eph=False):
  return await interaction.response.send_message(embed=CreateEmbed(
      title, desc, color),
                                          ephemeral=eph)


async def SendEmbed(interaction, embed, eph=False):
  return await interaction.response.send_message(embed=embed, ephemeral=eph)


async def SendDM(inter, title, desc, color):
  return await inter.user.send(embed=CreateEmbed(title, desc, color))


async def SendDMs(inter, embedList):
  return await inter.user.send(embeds=embedList)


async def EditMessage(message, newEmbed, color):
  newEmbed.color = color
  return await message.edit(embed=newEmbed)

async def DeleteMessage(serverId, channelId, messageId):
  bot = discordbot.GetBot()
  guild = bot.get_guild(serverId)
  if guild:
    channel = guild.get_channel(channelId)
    if channel:
      try:
        return await (await channel.fetch_message(messageId)).delete()
      except:
        print(f"SERVER: {serverId} deleted last spawn already")
        return


async def SendMessageNoInteraction(serverId, channelId, message):
  bot = discordbot.GetBot()
  guild = bot.get_guild(serverId)
  if guild:
    channel = guild.get_channel(channelId)
    if channel and not isinstance(channel,
                                  discord.ForumChannel) and not isinstance(
                                      channel, discord.CategoryChannel):
      await channel.send(message)

async def SendCommandResponse(interaction: Interaction, filename: str, command: str, responseInd: int, color, params: list=[], eph: bool=False):
  response = GetJson(filename)[command][responseInd]
  return await interaction.response.send_message(embed=CreateEmbed(
      response["Title"], response["Body"].format(*params), color), ephemeral=eph)


def CreateEmbed(title, desc, color):
  return Embed(title=title, description=desc, color=color)
