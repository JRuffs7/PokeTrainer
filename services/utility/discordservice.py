import logging
from discord import Embed, Interaction

from dataaccess.utility.jsonreader import GetJson

errorLogger = logging.getLogger('error')

async def SendEmbed(interaction: Interaction, embed: Embed):
  return await interaction.followup.send(embed=embed)


async def SendDMs(interaction: Interaction, embedList: list[Embed]):
  try:
    return await interaction.user.send(embeds=embedList)
  except Exception as e:
    errorLogger.error(f'DM Error: {e}')


async def SendCommandResponse(interaction: Interaction, filename: str, command: str, responseInd: int, color, params: list=[]):
  response = GetJson(filename)[command][responseInd]
  return await interaction.followup.send(embed=CreateEmbed(
      response["Title"], response["Body"].format(*params), color))


def CreateEmbed(title, desc, color, url = None, image: str = None, thumbnail: str = None, footerIcon: str = None, footer: str = None):
  embed = Embed(title=title, description=desc, color=color, url=url)
  embed.set_image(url=image)
  embed.set_thumbnail(url=thumbnail)
  embed.set_footer(icon_url=footerIcon,text=footer)
  return embed
