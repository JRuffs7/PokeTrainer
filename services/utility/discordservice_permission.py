from services.utility import discordservice
from discord import Interaction
from globals import ErrorColor

responseFile = "files/responsefiles/permissionresponses.json"

async def SendError(interaction: Interaction, permissionCheck: str):
  await discordservice.SendCommandResponse(interaction, responseFile, permissionCheck, 0, ErrorColor)