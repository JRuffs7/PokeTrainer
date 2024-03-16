from discord import Embed, Interaction

from dataaccess.utility.jsonreader import GetJson

async def SendEmbed(interaction: Interaction, embed: Embed, eph: bool = False):
  return await interaction.followup.send(embed=embed, ephemeral=eph)


async def SendDMs(interaction: Interaction, embedList: list[Embed]):
  return await interaction.user.send(embeds=embedList)


async def SendCommandResponse(interaction: Interaction, filename: str, command: str, responseInd: int, color, params: list=[], eph: bool=False):
  response = GetJson(filename)[command][responseInd]
  return await interaction.followup.send(embed=CreateEmbed(
      response["Title"], response["Body"].format(*params), color), ephemeral=eph)


def CreateEmbed(title, desc, color):
  return Embed(title=title, description=desc, color=color)
