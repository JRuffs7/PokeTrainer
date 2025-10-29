from discord import Guild
from dataaccess import serverda
from models.Server import Server


def RegisterServer(guild: Guild, channelId: int):
  if (not guild) or (not channelId):
    return None
  currServ = GetServer(guild.id)
  if not currServ:
    return None
  currServ.ChannelId = channelId
  UpsertServer(currServ)
  return currServ

#region Data

def CheckServer(serverId: int):
  return serverda.CheckServer(serverId)

def GetServer(serverId: int):
  return serverda.GetSingleServer(serverId)

def GetAllServers():
  return serverda.GetAllServers()

def UpsertServer(server: Server):
  return serverda.UpsertSingleServer(server)

def DeleteServer(server: Server):
  return serverda.DeleteSingleServer(server)

#endregion
